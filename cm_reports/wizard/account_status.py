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
        if self.env.context.get('export_excel'):
            return self.env.ref('cm_reports.report_account_status_xls').report_action(self, data = datas)

        return self.env.ref('cm_reports.account_status_report_account_status').report_action(self, data = datas)
