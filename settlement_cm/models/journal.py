# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _

class inherit_account_journal(models.Model):
    _inherit='account.journal'

    request_card_data = fields.Boolean(string='Solicitar datos de tarjeta')
    valid_for_cash_register = fields.Boolean(string='Valido para registro de caja')
    valid_for_payments = fields.Boolean(string='Valido para pagos')
    user_ids = fields.Many2many('res.users', string='Usuarios permitidos')