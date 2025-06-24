# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _

class inherit_register_payments(models.TransientModel):
    _inherit='account.payment.register'


    # cash_register_id = fields.Many2one('cash.register', string='Cierre de caja')
    type = fields.Selection([('bank','Banco'),('cash','Efectivo')], string='Tipo')
    request_card_data = fields.Boolean(string='Solicitar Data')
    nro_auto = fields.Char(string='Nro AUTO')
    card_digits = fields.Char(string='Digitos de tarjeta')
    user_id = fields.Many2one('res.users',string='Usuario',default=lambda self: self.env.user)

    @api.onchange('journal_id')
    def onchange_journal_type(self):
        self.type = self.journal_id.type
        self.request_card_data = self.journal_id.request_card_data

    def _create_payment_vals_from_wizard(self, batch_result):
        res = super(inherit_register_payments, self)._create_payment_vals_from_wizard(batch_result)
        res.update({'nro_auto': self.nro_auto, 'card_digits': self.card_digits, 'user_id': self.user_id.id, 'request_card_data': self.request_card_data})
        return res