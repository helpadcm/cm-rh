# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class priceListHandling(models.Model):
    _name = 'pricelist.handling'
    _description = "Listas de precio encomiendas"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string="Nombre")
    initial_date = fields.Date(string="Fecha de Inicio")
    final_date = fields.Date(string="Fecha de Finalizacion")
    applicable = fields.Selection([('permanent','Permanente'),('temporal','Temporal')], string="Aplicable", default='permanent')
    rutes_ids = fields.Many2many('cargo.airport.airport.rel',string="Disponible en rutas")
    active = fields.Boolean(string="Activo", default=True)
    list_product_ids = fields.One2many('pricelist.product.handling','list_id',string="Lista de productos")
    fare_class_id = fields.Many2one('fare.clases',string="Clase Tarifaria")
    default_list = fields.Boolean(string="Lista por defecto")

class productListHandling(models.Model):
    _name = 'pricelist.product.handling'
    _description = "Productos lista de precios encomiendas"

    @api.model
    def get_default_currency(self):
        usd_currency_id = self.env.ref('base.USD')
        return usd_currency_id.id

    product_id = fields.Many2one('product.product',string="Producto")
    udm_id = fields.Many2one('uom.uom',string="Udm")
    price = fields.Monetary(string="Precio")
    qty_min = fields.Float(string="Minimo")
    list_id = fields.Many2one('pricelist.handling', string="Lista de precio")
    currency_id = fields.Many2one('res.currency',string="Moneda", default=get_default_currency)

    @api.onchange('product_id')
    def change_product(self):
        if self.product_id:
            self.udm_id = self.product_id.uom_id.id