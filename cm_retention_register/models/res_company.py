# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class res_company(models.Model):
	_inherit = 'res.company'

	@api.model
	def default_sequence_retention(self):
		for sequence in self.env.get('ir.sequence').search([('code','=','retentions.number')]):
			return sequence.id
		return False

	retention_sequence_id = fields.Many2one("ir.sequence",string="Secuencia de retencion",default=default_sequence_retention)

	