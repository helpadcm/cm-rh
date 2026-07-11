from odoo import api, exceptions, models,fields, _
from datetime import datetime

class RentProductSize(models.Model):
    _name = 'cargo.rent.product.size'
    _description = "Tamaños de producto"

    name = fields.Char('Nombre')
    currency_id = fields.Many2one('res.currency',string="Moneda")
    price = fields.Monetary(currency_field="currency_id",string="Precio")
    rent_product_id = fields.Many2one('cargo.rent.product',string="Producto en Alquiler")

class RentProduct(models.Model):
    _name = 'cargo.rent.product'
    _description = "Productos en alquiler"

    ref = fields.Char(string="Codigo")
    name = fields.Char(string="Nombre")
    state = fields.Selection([('in_use','En uso'),('free','Libre'),('Damaged','Dañado'),('lost','Perdido')], default="free")
    size_ids = fields.One2many('cargo.rent.product.size','rent_product_id',string="Tamaños")