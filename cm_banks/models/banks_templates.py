# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _

class bank_template(models.Model):
	_name = 'banks.template'
	_description = "Plantillas Bancarias"
	
	def _get_user_id(self):
		result={}
		result[ids]=uid
		return result

	doc_type= fields.Selection([
					('check','Cheque'),
					('transference','Transferencia'),
					('deposit','Deposito'),
					('debit','Debito'),
					('credit','Credito'),
					('banks_transferencest','Transferencia Bancaria')], string='Tipo Doc.')
	name=fields.Char(string='Nombre', required=True)
	doc_id= fields.Integer(string='Doc')
	journal_comp_id= fields.Integer(string='Journal company id')




