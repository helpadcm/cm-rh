# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ap_account_payment(models.Model):
	_inherit='account.payment'

	was_unreconcilied = fields.Boolean(string='Desconciliado')
	deposit_id = fields.Many2one('banks.deposit', string='Deposit Ref')
	analytic_account_id	=	fields.Many2one('account.analytic.account', string='Cuenta Analitica')
	number_doc = fields.Char(string = 'Numero')
	write_off_line = fields.One2many('account.payment.writeoffline','payment_id',string="Write off lines")
	pay_method_type= fields.Selection([
				('check','Cheque'),
				('transference','Transferencia'),
				('otros','Otros')], string='Tipo de Transaccion')

	def action_post(self):
		res = super(ap_account_payment, self).action_post()
		if self.partner_type == 'supplier':
			sequence_id = self.journal_id.sequence_ids.filtered(lambda seq: seq.code2.code == self.pay_method_type)
			if sequence_id:
				self.name = sequence_id.next_by_id()
		return res
