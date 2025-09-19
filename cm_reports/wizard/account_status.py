# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import base64

class wizard_account_status(models.TransientModel):
    _name = "cm_reports.wizard_account_status"
    _description = "Estado de cuenta Clientes"

    date_to = fields.Date(string="Fecha Final")
    date_start = fields.Date(string="Fecha de Inicio")
    partner_id = fields.Many2one('res.partner',string="Cliente")
    partner_ids = fields.Many2many('res.partner',string="Clientes")
    payment_state = fields.Selection([('paid','Pagado Totalmente'),('pending','Pendientes de pago')],default="pending",string="Estado de pago")
    zero_balance    = fields.Boolean(string="Con Saldo Distinto de cero")

    def report_status(self):
        datas = {
            'date_to': self.date_to,
            'date_start': self.date_start,
            'partner_id': self.partner_id.ids,
            'partner_ids': self.partner_ids.ids,
            'zero_balance': self.zero_balance,
            'payment_state': self.payment_state
        }
        return self.env.ref('cm_reports.account_status_report_account_status').report_action(self, data = datas)
    
    # def report_pdf(self):
    #     res= self.env['report'].get_pdf(self.ids, 'account_status.report_account_status')
    #     Attachment = self.env['ir.attachment']
    #     report_name="account_status.pdf"
    #     result = base64.b64encode(res)
    #     attachment_ids=[]
    #     attachment_data = {
    #         'name': report_name,
    #         'datas_fname': report_name,
    #         'datas':result,
    #         'type': 'binary',
    #         'res_model': 'res.partner',
    #         #'res_id': mail.mail_message_id.id,
    #     }
    #     attachment_ids.append(Attachment.create(attachment_data).id)
    #     return self.partner_id.action_quotation_send(attachment_ids)
    #     return res

    # @api.constrains('date_start','date_to')
    # def valid_dates(self):
    #     if self.date_start and self.date_to:
    #         if self.date_start > self.date_to:
    #             raise ValidationError("La fecha inicial no puede ser mayor que la fecha final")

    # def export_xls(self,datas):
    #     datas = {}
    #     datas['model'] = 'account.invoice'
    #     datas['form'] = self.read(['date_to', 'date_start','partner_id','partner_ids','show_detail','configuration','use_start_date','zero_balance'])[0]
    #     used_context = self.env.context
    #     datas['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'es'))
    #     context = self._context
    #     return {'type': 'ir.actions.report.xml',
    #             'report_name': 'account_status.account_status_xls.xlsx',
    #             'datas': datas,
    #             'name': 'Account Status XLS'}
