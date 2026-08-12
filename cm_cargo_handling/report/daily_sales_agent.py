from odoo import models,api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from reportlab.graphics import renderPM
from base64 import b64encode
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Drawing
from reportlab.lib import units
from collections import OrderedDict

class dailySalesAgent(models.AbstractModel):
    _name = 'report.cm_cargo_handling.daily_sales_agent'
    _description = "Ventas Diarias"
 
    @api.model
    def _get_report_values(self, docids, data=None):
        info = self.get_data(data)
        initial_date_obj = datetime.strptime(data.get('start_date'), "%Y-%m-%d")
        formated_initial_date = initial_date_obj.strftime("%d/%m/%Y")
        final_date_obj = datetime.strptime(data.get('final_date'), "%Y-%m-%d")
        formated_final_date = final_date_obj.strftime("%d/%m/%Y")
        return {
            'data': info,
            'initial_date': formated_initial_date,
            'final_date': formated_final_date
        }

    def get_data(self, data):
        employees = data.get('employee_ids')
        start_date = data.get('start_date')
        final_date = data.get('final_date')

        payment_ids = self.env['account.payment'].search(
            [
                ('user_id', 'in', employees),
                ('date', '>=', start_date),
                ('date', '<=', final_date),
                ('state', 'in', ['in_process', 'paid'])
            ],
            order='date,user_id'
        )

        days = OrderedDict()

        for payment in payment_ids:

            date = payment.date

            if date not in days:
                days[date] = {}

            if payment.user_id.id not in days[date]:
                days[date][payment.user_id.id] = {
                    'employee': payment.user_id.name,
                    'total_cash_lps': 0,
                    'total_cash_usd': 0,
                    'total_credit_lps': 0,
                    'total_credit_usd': 0,
                    'total_transfer_lps': 0,
                    'total_transfer_usd': 0,
                    'total_lps': 0,
                    'total_usd': 0,
                }

            employee = days[date][payment.user_id.id]

            if payment.journal_id.code == 'EFU':
                employee['total_cash_lps'] += payment.amount_company_currency_signed
                employee['total_cash_usd'] += payment.total_usd

            elif payment.journal_id.code == 'TRBKS':
                employee['total_transfer_lps'] += payment.amount_company_currency_signed
                employee['total_transfer_usd'] += payment.total_usd

            elif payment.journal_id.code != 'PGCM':
                employee['total_credit_lps'] += payment.amount_company_currency_signed
                employee['total_credit_usd'] += payment.total_usd

            employee['total_lps'] = (
                employee['total_cash_lps'] +
                employee['total_credit_lps'] +
                employee['total_transfer_lps']
            )

            employee['total_usd'] = (
                employee['total_cash_usd'] +
                employee['total_credit_usd'] +
                employee['total_transfer_usd']
            )

        result = []

        for date, employees in days.items():
            result.append({
                'date': self.change_format(date),
                'employees': list(employees.values())
            })

        return result

    def change_format(self,date):
        if date:
            formato_fecha = "%d/%m/%Y"
            # fecha_inicial = datetime.strptime(date, "%Y-%m-%d")
            fecha = datetime.strftime(date,formato_fecha)
            return fecha