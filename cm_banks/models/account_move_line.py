# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import datetime
import time

class banks_account_move_line(models.Model):
	_inherit = 'account.move.line'

	credit_debit_id = fields.Many2one('debit.credit', string='Debito/Credito')
	mcheck_id = fields.Many2one('mcheck.mcheck', string='mcheck')
	deposit_id=fields.Many2one('banks.deposit', string='Deposito')

class res_currency_inherites(models.Model):
	_inherit = 'res.currency'
	
	base = fields.Boolean(string='Base')