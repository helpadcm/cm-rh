# -*- coding: utf-8 -*-
from odoo import api, exceptions, models, fields, _

class discountList(models.Model):
    _name = 'cargo.discount'
    _description = "Lista de Descuentos"

    name = fields.Char(string="Nombre")
    is_active = fields.Boolean("Esta Activo")
    porcentage = fields.Float(string="Porcentaje")
    user_ids = fields.Many2many('res.users',string="Para Usuarios")
    product_ids = fields.Many2many('product.product', string="Para Productos")