# -*- coding: utf-8 -*-
from odoo import api, exceptions, models, fields, _

list_discount_types = [
    ('clients','Clientes'),
    ('cargo','Encomiendas'),
    ('promo','Promociones')
]

class discountList(models.Model):
    _name = 'cargo.discount'
    _description = "Lista de Descuentos"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string="Nombre", tracking=True)
    is_active = fields.Boolean("Esta Activo", tracking=True)
    porcentage = fields.Float(string="Porcentaje", tracking=True)
    user_ids = fields.Many2many('res.users',string="Para Usuarios")
    product_ids = fields.Many2many('product.product', string="Para Productos")
    discount_by = fields.Selection([('weight','Peso'),('percentage','Porcentaje')], string="Descuento por", default="percentage", tracking=True)
    discount_weight = fields.Float(string="Peso", tracking=True)
    code = fields.Char(string="Código", tracking=True)
    available_for = fields.Selection(list_discount_types, string="Disponible para", tracking=True)