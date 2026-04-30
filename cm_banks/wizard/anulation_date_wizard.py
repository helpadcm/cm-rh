# -*- coding: utf-8 -*-

import time
from odoo import models, fields, api, _

class anullation_date_wizard(models.TransientModel):
	_name = 'anullation_date_wizard'
	_description = "Anulacion de fecha"
	
	date = fields.Date(string='Fecha', help="Fecha efectiva de anuacion", required=True, default=lambda self: self._context['date'] if self._context and  self._context['date'] not in [False,None] else  False)
	journal_id = fields.Many2one('account.journal', string='Diario', required=False, default=lambda self:self._context['journal_id'] if self._context and  self._context['journal_id'] not in [False,None] else  False)
	date_mcheck = fields.Date(string='Fecha de pago',  help="Fecha", required=False )
	debit_credit_id = fields.Many2one('debit.credit','Debito/Credito')
	only_one = fields.Boolean(string='Solo un movimiento')

	def anulate_doc(self):
		self.env.context = dict(self.env.context or {})
		#context.update({'only_one':True})	
		if self.env.context.get('active_id'):
			self.env['mcheck.mcheck'].browse(self.env.context.get('active_id')).cancel_payment(self.date)
		else:
			raise osv.except_osv("La operacion no pudo finalizar, intente de nuevo!")