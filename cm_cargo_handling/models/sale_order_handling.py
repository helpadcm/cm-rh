# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

states = [
    ('quote','Cotizacion'),
    ('order','Orden')
]

class saleOrderHandling(models.Model):
    _name = 'sale.order.handling'
    _description = "Ordenes de venta encomiendas"
    _inherit = ['mail.thread','mail.activity.mixin']

    @api.model
    def user_default(self):
        return self.env.user.id

    @api.model
    def origin_default(self):
        if not self.env.user.station_id:
            raise ValidationError("¡¡Su usuario no cuenta con una estacion configurada por defecto, por favor contacte con el administrador!!")
        return self.env.user.station_id.id

    @api.model
    def default_date(self):
        return datetime.now()

    @api.model
    def default_get(self, fields):
        lps_currency_id = self.env.ref('base.HNL')
        usd_currency_id = self.env.ref('base.USD')
        rec = super(saleOrderHandling, self).default_get(fields)
        context = dict(self._context or {})
        active_ids = context.get('active_ids')
        rec.update({
            'local_currency_id': lps_currency_id.id,
            'external_currency_id': usd_currency_id.id
        })
        return rec


    name = fields.Char(string="Numero de orden", default="Borrador", tracking=True)
    origin_id = fields.Many2one('cargo.station', string="Origen", default=origin_default, tracking=True)
    destination_id = fields.Many2one('cargo.station', string="Destino", tracking=True)
    user_id = fields.Many2one('res.users', string="Agente", default=user_default, tracking=True)
    product_id = fields.Many2one('product.product',string="Producto")
    udm_id = fields.Many2one('uom.uom',string="Udm")
    pricelist_id = fields.Many2one('pricelist.handling',string="Lista de Precio")
    date = fields.Datetime(string="Fecha de registro",default=default_date)
    local_currency_id = fields.Many2one('res.currency',string="Moneda Local")
    external_currency_id = fields.Many2one('res.currency',string="Moneda Extranjera")
    weight_or_qty = fields.Float(string="Cantidad", help="En este campo se debe agregar el peso en lbs o la cantidad de unidades, esto de acuerdo al producto que se este seleccionando")
    local_price = fields.Float(string="Precio Lps", compute="calculate_amounts", store=True)
    external_price = fields.Float(string="Precio USD", compute="calculate_amounts", store=True)
    state = fields.Selection(states, string="Estado", default="quote", tracking=True)
    cart_ids = fields.One2many('cart.order.handling', 'order_id', string="Carrito de ordenes")
    listprice_domain = fields.Binary(string="Dominio de lista de precios", compute="update_pricelist")
    partner_id = fields.Many2one('res.partner',string="Cliente", tracking=True)

    @api.depends('origin_id', 'destination_id', 'partner_id')
    def update_pricelist(self):
        for rec in self:
            domain = [('id','=',0)]
            if rec.origin_id and rec.destination_id:
                airports_rel_ids = self.env['cargo.airport.airport.rel'].search([('origin_id.id','=',rec.origin_id.airport_id.id),('destination_id','=',rec.destination_id.airport_id.id)])
                if airports_rel_ids:
                    list_price_ids = self.env['pricelist.handling'].search([('rutes_ids','in',airports_rel_ids.ids)])
                    if list_price_ids:
                        if rec.partner_id.default_client:
                            domain = [('id','in',list_price_ids.ids)]
                        else:
                            domain = [('id','in',list_price_ids.ids),('fare_class_id','in',rec.partner_id.fare_classes_ids.ids)]
                    else:
                        domain = [('id','=',0)]
                else:
                    domain = [('id','=',0)]
            else:
                domain = [('id','=',0)]

            rec.listprice_domain = domain

    @api.onchange('product_id', 'pricelist_id', 'weight_or_qty')
    def change_product(self):
        if self.product_id:
            self.udm_id = self.product_id.uom_id.id

    @api.depends('product_id', 'pricelist_id', 'weight_or_qty')
    def calculate_amounts(self):
        for rec in self:
            if rec.pricelist_id and rec.product_id:
                if not rec.pricelist_id:
                    raise ValidationError("Debe seleccionar una lista de precio")

                if not rec.product_id:
                    raise ValidationError("Debe seleccionar un producto")
                    
                line_id = rec.pricelist_id.list_product_ids.filtered(lambda line: line.product_id.id == rec.product_id.id)
                if line_id:
                    price = 0
                    if rec.weight_or_qty > 0:
                        if rec.weight_or_qty <= line_id.qty_min:
                            price = line_id.price * line_id.qty_min
                        else:
                            price = line_id.price * rec.weight_or_qty

                    rec.external_price = price
                    rec.local_price = rec.external_currency_id._convert(price, rec.local_currency_id, self.env.company, rec.date, True)
                else:
                    raise ValidationError("No hay regla de precio para el producto seleccionado en la lista de precio")

    def add_cart(self):
        if not self.product_id:
            raise ValidationError("Debe seleccionar un producto")

        if self.weight_or_qty <= 0:
            raise ValidationError("La cantidad debe ser mayor de cero")

        if self.weight_or_qty > 0:
            self.env['cart.order.handling'].create({
                'order_id': self.id,
                'product_id': self.product_id.id,
                'udm_id': self.udm_id.id,
                'local_currency_id': self.local_currency_id.id,
                'external_currency_id': self.external_currency_id.id,
                'weight_or_qty': self.weight_or_qty,
                'local_price': self.local_price,
                'external_price': self.external_price,
                'partner_id': self.partner_id.id
            })
            self.weight_or_qty = 0
            self.local_price = 0 
            self.external_price = 0
        return True

    def change_states(self):
        state_type = self.env.context.get('state')
        if state_type:
            if state_type == 'order':
                self.create_guides()
            self.state = state_type

    def create_guides(self):
        if not self.cart_ids:
            raise ValidationError("No hay nada agregado al carrito")

        if self.name == 'Borrador':
            sequence_id = self.env.ref('cm_cargo_handling.sequence_sale_order_handling')
            if sequence_id:
                self.name = sequence_id.next_by_id()

class orderCartHandling(models.Model):
    _name = 'cart.order.handling'
    _description = "Carrito de ordenes"

    product_id = fields.Many2one('product.product',string="Producto")
    udm_id = fields.Many2one('uom.uom',string="Udm")
    local_currency_id = fields.Many2one('res.currency',string="Moneda Local")
    external_currency_id = fields.Many2one('res.currency',string="Moneda Extranjera")
    weight_or_qty = fields.Float(string="Cantidad", help="En este campo se debe agregar el peso en lbs o la cantidad de unidades, esto de acuerdo al producto que se este seleccionando")
    local_price = fields.Float(string="Precio Lps")
    external_price = fields.Float(string="Precio USD")
    order_id = fields.Many2one('sale.order.handling',string="Orden de Venta")
    partner_id = fields.Many2one('res.partner',string="Cliente")