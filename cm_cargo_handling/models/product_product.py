from odoo import api, exceptions, models,fields, _
from datetime import datetime

class ProductTemplateInherit(models.Model):
	_inherit = 'product.template'

	type_cargo = fields.Many2one('cargo.type','Tipo de Envio')
	for_cargo = fields.Boolean(string='Para carga?')
	for_recargo = fields.Boolean(string='Para Cargo Adicional?')

class ProductProductInherit(models.Model):
	_inherit = 'product.product'

	type_cargo = fields.Many2one(related="product_tmpl_id.type_cargo", string="Tipo de Envio")