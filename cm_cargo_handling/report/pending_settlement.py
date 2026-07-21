from odoo import models,api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from reportlab.graphics import renderPM
from base64 import b64encode
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Drawing
from reportlab.lib import units
from collections import OrderedDict

class pendingSettlementReport(models.AbstractModel):
    _name = 'report.cm_cargo_handling.pending_settlement_report'
    _description = "Pendientes de liquidar"
 
    @api.model
    def _get_report_values(self, docids, data=None):
        info = self.get_data(data)
        initial_date_obj = datetime.strptime(data.get('initial_date'), "%Y-%m-%d")
        formated_initial_date = initial_date_obj.strftime("%d/%m/%Y")
        final_date_obj = datetime.strptime(data.get('final_date'), "%Y-%m-%d")
        formated_final_date = final_date_obj.strftime("%d/%m/%Y")
        return {
            'data': info,
            'initial_date': formated_initial_date,
            'final_date': formated_final_date
        }

    def get_data(self, data):
        initial_date = data.get('initial_date')
        final_date = data.get('final_date')
        user_id = self.env.user
        employee_ids = False
        if self.env.user.has_group("cm_cargo_handling.group_guia_cargar_admin"):
            employee_ids = self.env['hr.employee'].search([])
        else:
            employee_id = self.env['hr.employee'].search([('user_id','=',user_id.id)])
            employee_ids = self.env['hr.employee'].search([('parent_id','=',employee_id.id)])
        
        result_ids = employee_ids.mapped('user_id')

        payment_ids = self.env['account.payment'].search([('date','>=',initial_date),('date','<=',final_date),('user_id','in',result_ids),('partner_type','=','customer'),('state','in',['paid','in_process'])])
        data = []
        user_ids = []
        for payment in payment_ids:
            if not payment.cash_register_id or payment.cash_register_id.state == 'draft':
                state = ''
                if payment.cash_register_id:
                    state = payment.cash_register_id._fields['state'].convert_to_export(payment.cash_register_id.state, payment.cash_register_id)
                vals = {
                    'number': payment.name,
                    'date': payment.date.strftime('%d/%m/%Y'),
                    'journal': payment.journal_id.name,
                    'usd_amount': payment.total_usd,
                    'lps_amount': payment.amount_company_currency_signed,
                    'cash_state': state
                }
                if payment.user_id.id in user_ids:
                    data[user_ids.index(payment.user_id.id)]['info'].append(vals)
                else:
                    user_ids.append(payment.user_id.id)
                    data.append({
                        'user': payment.user_id.name,
                        'info': [vals]})
        return data