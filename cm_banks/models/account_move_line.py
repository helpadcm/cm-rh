# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import datetime
import time

class banks_account_move_line(models.Model):
	_inherit = 'account.move.line'

	credit_debit_id = fields.Many2one('debit.credit', string='Debito/Credito')
	mcheck_id = fields.Many2one('mcheck.mcheck', string='mcheck')
	deposit_id=fields.Many2one('banks.deposit', string='Deposito')

	def compute_amount_fields(self, amount, src_currency, company_currency, invoice_currency=False):
		""" Helper function to compute value for fields debit/credit/amount_currency based on an amount and the currencies given in parameter """
		amount_currency = amount
		currency_id = company_currency
		date = self.date or fields.Date.context_today(self)
		company = self.company_id

		if src_currency and src_currency.id != company_currency.id:
			amount_currency = amount
			amount = src_currency._convert(amount, company_currency, company, date)
			currency_id = src_currency.id

		debit = amount if amount > 0 else 0.0
		credit = -amount if amount < 0 else 0.0

		if invoice_currency and invoice_currency.id != company_currency.id and not amount_currency:
			amount_currency = company_currency._convert(amount, invoice_currency, company, date)
			currency_id = invoice_currency.id
		return debit, credit, amount_currency, currency_id

class res_currency_inherites(models.Model):
	_inherit = 'res.currency'
	
	base = fields.Boolean(string='Base')