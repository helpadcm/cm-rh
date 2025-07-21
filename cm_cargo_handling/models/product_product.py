from odoo import api, exceptions, models,fields, _
from datetime import datetime
from odoo.exceptions import ValidationError

class ProductTemplateInherit(models.Model):
	_inherit = 'product.template'

	type_cargo = fields.Many2one('cargo.type','Tipo de Envio')
	for_cargo = fields.Boolean(string='Para carga?')
	for_recargo = fields.Boolean(string='Para Cargo Adicional?')
	price_list_ids = fields.One2many('pricelist.product', 'product_id', string="Lista de precios")
	rute_ids = fields.Many2many('cargo.airport.airport.rel', string="Rutas")
	price = fields.Monetary(string="Precio")
	qty_min = fields.Float(string="Minimo")

	def add_routes(self):
		route_ids = self.env['cargo.airport.airport.rel'].search([])
		if len(self.price_list_ids) == 0:
			for route in route_ids:
				self.env['pricelist.product'].create({
					'product_id': self.id,
					'rute_id': route.id
				})
		else:
			existing_routes_ids = self.price_list_ids.mapped('rute_id').ids
			for route in route_ids:
				if route.id not in existing_routes_ids:
					self.env['pricelist.product'].create({
						'product_id': self.id,
						'rute_id': route.id
					})
					
	def add_values(self):
		if not self.rute_ids:
			raise ValidationError("Debe seleccionar una o mas rutas.")

		if self.price_list_ids:
			for line in self.price_list_ids:
				if line.rute_id.id in self.rute_ids.ids:
					line.price = self.price
					line.qty_min = self.qty_min

			self.rute_ids = False
			self.price = 0
			self.qty_min = 0
		else:
			raise ValidationError('No existe lista de precios creada')

class ProductProductInherit(models.Model):
	_inherit = 'product.product'

	type_cargo = fields.Many2one(related="product_tmpl_id.type_cargo", string="Tipo de Envio")


class priceListProduct(models.Model):
	_name = "pricelist.product"
	_description = "Lista de precios por producto"

	@api.model
	def get_default_currency(self):
		usd_currency_id = self.env.ref('base.USD')
		return usd_currency_id.id
		
	product_id = fields.Many2one('product.template',string="Producto")
	rute_id = fields.Many2one('cargo.airport.airport.rel',string="Ruta")
	price = fields.Monetary(string="Precio")
	qty_min = fields.Float(string="Minimo")
	currency_id = fields.Many2one('res.currency',string="Moneda", default=get_default_currency)