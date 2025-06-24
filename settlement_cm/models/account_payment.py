# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _

class inherit_payment(models.Model):
    _inherit = 'account.payment'

    @api.onchange('journal_id')
    def onchange_journal_type(self):
        self.type = self.journal_id.type
        self.request_card_data = self.journal_id.request_card_data
        
    # cash_register_id	=	fields.Many2one('cash.register', string='Registro de Caja')
    type = fields.Selection([('bank','Bank'),('cash','Cash')], string='Tipo')
    request_card_data = fields.Boolean(string='Solicitar Data')
    nro_auto = fields.Char(string='Nro AUTO')
    card_digits = fields.Char(string='Digitos de tarjeta')
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user)	

