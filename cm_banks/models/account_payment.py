# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ap_account_payment(models.Model):
	_inherit='account.payment'

	was_unreconcilied = fields.Boolean(string='Desconciliado')
	deposit_id = fields.Many2one('banks.deposit', string='Deposit Ref')
	payment_date = fields.Date(tracking=True)
	pay_method_type= fields.Selection([
				('check','Cheque'),
				('transference','Transferencia'),
				('otros','Otros')], string='Tipo de Transaccion')