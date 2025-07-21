# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

states = [
    ('quote', 'Cotizacion'),
    ('order', 'Orden'),
    ('invoiced', 'Finalizado')
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
    bill_lading_ids = fields.One2many('cargo.bill', 'order_id', string="Guias de Carga")
    has_contacts = fields.Boolean(string="Tiene contactos")
    content_description_ids = fields.Many2many('cargo.content.description', string="Descripcion del Contenido")
    apply_rtn = fields.Boolean(string="Agregar RTN")
    rtn = fields.Char(string="RTN")
    modality = fields.Selection([('upon_delivery','Por Cobrar'),('credit','Credito'),('counted','Contado')], string="Modalidad", default="counted")
    type_id = fields.Many2one(related="product_id.type_cargo",string="Tipo de carga")
    options	= fields.Selection(related="type_id.options", string="Tipo")
    content_description = fields.Text(string="Descripcion", tracking=True)
    observations = fields.Text(string="Observaciones", tracking=True)
    pieces_qty = fields.Integer(string="Piezas",default=1, tracking=True)
    piece_type = fields.Selection([('uniform','Uniforme'),('mix','Mixta')], string="Tipo de pieza", tracking=True, default="uniform")
    additional_services_ids = fields.One2many('cargo.bill.additional.service', 'order_id', string="Servicios Adicionales")
    qty_guides = fields.Integer(string="Cant. Guias", compute="calculate_total_guides")
    allow_create_guides = fields.Boolean(string="Crear guias?")
    created_guides = fields.Boolean(string="Guias Creadas")
    parent_id = fields.Many2one('res.partner',string="Fact. Autorizados")
    readonly_rtn = fields.Boolean(string="RTN solo lectura")
    default_client = fields.Boolean(string="Cliente por defecto")
    # Sender
    sender_id = fields.Many2one('res.partner.contact',string="Remitente", tracking=True)
    sender_name = fields.Char(string="Nombre Remitente", tracking=True)
    id_sender = fields.Char(string="Identidad Remitente", tracking=True)
    sender_phone = fields.Char(string="Telefono Remitente", tracking=True)
    # lost_reason_id = fields.Many2one("crm.lost.reason", "Motivo DESECHADA")
    # Receiver
    receiver_id = fields.Many2one('res.partner.contact',string="Destinatario", tracking=True)
    receiver_name = fields.Char(string="Nombre Destinatario", tracking=True)
    id_receiver = fields.Char(string="Identidad Destinatario", tracking=True)
    receiver_phone = fields.Char(string="Telefono Destinatario", tracking=True)

    weight = fields.Float(string="Peso LBS", compute="calculate_totals", store=True)
    preliminar_price = fields.Float(string="Precio preliminar ($)", compute='calculate_totals', store=True)
    amount_tax = fields.Float(string="Isv", compute='calculate_totals', store=True)
    amount_untaxed = fields.Float(string="Base imponible", compute='calculate_totals', store=True)
    amount_total = fields.Float(string="Total", compute='calculate_totals', store=True)
    total = fields.Float(string="Subtotal", compute='calculate_totals', store=True)
    amount_total_lps = fields.Float(string="Total (Lps)", compute='calculate_totals', store=True)
    additional_costs = fields.Float(string="Costos Adicionales ($)", compute='calculate_totals',store=True)

    move_id = fields.Many2one('account.move',string="Factura")
    payment_state = fields.Selection(string="Estado de Pago", related="move_id.payment_state")

    @api.onchange('modality', 'default_client')
    def allow_create_handling(self):
        if self.modality == 'upon_delivery':
            self.allow_create_guides = True
        else:
            self.allow_create_guides = False

        if not self.default_client and self.modality != 'credit':
            self.readonly_rtn = False

    def show_bill_ladings(self):
        return {
            'name': _('Guias de Carga'),
            'type': 'ir.actions.act_window',
            'res_model': 'cargo.bill',
            'view_mode': 'tree,form',
            'domain': [('order_id', '=', self.id)],
            'target': 'current',
            'context': {'default_order_id': self.id},
        }

    def show_invoice(self):
        return {
            'name': _('Factura de encomienda'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.move_id.id,
            'target': 'current',
            'context': {},
        }

    def register_payment(self):
        self.move_id.action_post()
        return self.move_id.line_ids.action_register_payment()

    @api.depends('cart_ids')
    def calculate_total_guides(self):
        for rec in self:
            rec.qty_guides = sum(rec.cart_ids.mapped('pieces_qty'))

    @api.depends('cart_ids','product_id', 'origin_id', 'destination_id', 'modality', 'additional_services_ids')
    def calculate_totals(self):
        for rec in self:
            total_lbs = 0
            total_dls = 0
            additional_cost = 0
            total_included = 0
            if rec.origin_id:
                additional_cost += rec.origin_id.internal_load_ori
            if rec.destination_id:
                additional_cost += rec.destination_id.internal_load_dest

            if rec.additional_services_ids:
                additional_cost += sum(rec.additional_services_ids.mapped('total'))

            if rec.modality in ['upon_delivery','credit']:
                additional_cost += 1

            rec.additional_costs = additional_cost

            for line in rec.cart_ids:
                total_lbs += line.weight_or_qty
                total_dls += line.external_price
            
            subtotal = total_dls + additional_cost
            rec.weight = total_lbs
            rec.preliminar_price = total_dls
            rec.amount_untaxed = subtotal
            rec.total = subtotal


            taxes = rec.product_id.taxes_id.compute_all(subtotal, rec.external_currency_id, 1, product=rec.product_id, partner=False)
            if taxes:
                rec.amount_tax = taxes['total_included'] - taxes['total_excluded']
                total_included = taxes['total_included']
            
            rec.amount_total = total_included
            rec.amount_total_lps = rec.external_currency_id._convert(rec.amount_total, rec.local_currency_id, self.env.company, rec.date, True)


    @api.onchange('partner_id')
    def show_contacts(self):
        self.receiver_id = False
        self.id_receiver = False
        self.id_sender = False
        self.sender_id = False
        self.sender_phone = False
        self.receiver_phone = False

        if self.partner_id:
            if self.partner_id.default_client:
                self.has_contacts = False
                self.default_client = True
                self.apply_rtn = False
                self.rtn = False
                self.modality = 'counted'
                self.readonly_rtn = False
            else:
                self.has_contacts = True
                self.apply_rtn = True
                self.rtn = self.partner_id.vat
                self.modality = self.partner_id.modality

                if self.partner_id.modality == 'credit':
                    self.readonly_rtn = True
                else:
                    self.readonly_rtn = False

    @api.onchange('parent_id')
    def change_parent(self):
        if self.parent_id:
            self.rtn = self.parent_id.vat
    
    @api.onchange('receiver_id','sender_id')
    def get_data_contacts(self):
        if self.receiver_id:
            self.id_receiver = self.receiver_id.identity
            self.receiver_phone = self.receiver_id.phone
        if self.sender_id:
            self.id_sender = self.sender_id.identity
            self.sender_phone = self.sender_id.phone

    @api.depends('origin_id', 'destination_id', 'partner_id')
    def update_pricelist(self):
        for rec in self:
            domain = [('id','=',0)]
            if rec.origin_id and rec.destination_id:
                airports_rel_ids = self.env['cargo.airport.airport.rel'].search([('origin_id.id','=',rec.origin_id.airport_id.id),('destination_id','=',rec.destination_id.airport_id.id)])
                if airports_rel_ids:
                    list_price_ids = self.env['pricelist.handling'].search(['|',('rutes_ids','in',airports_rel_ids.ids),('all_available','=',True)])
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
            if rec.product_id:
                line_id = False
                if not rec.pricelist_id:
                    line_id = rec.product_id.price_list_ids.filtered(lambda line: line.rute_id.origin_id.id == rec.origin_id.airport_id.id and line.rute_id.destination_id.id == rec.destination_id.airport_id.id)
                else:
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
        if self.cart_ids:
            total_qty = sum(self.cart_ids.mapped('pieces_qty'))
            if total_qty == self.pieces_qty:
                raise ValidationError("No puede agregar mas lineas al carrito, la cantidad de piezas no puede ser mayor")

        if self.weight_or_qty <= 0:
            raise ValidationError("La cantidad debe ser mayor de cero")

        if self.weight_or_qty > 0:
            pieces = 1
            if self.piece_type == 'uniform':
                pieces = self.pieces_qty

            self.env['cart.order.handling'].create({
                'order_id': self.id,
                'product_id': self.product_id.id,
                'udm_id': self.product_id.uom_id.id,
                'local_currency_id': self.local_currency_id.id,
                'external_currency_id': self.external_currency_id.id,
                'weight_or_qty': self.weight_or_qty,
                'local_price': self.local_price * pieces,
                'external_price': self.external_price * pieces,
                'partner_id': self.partner_id.id,
                'pieces_qty': pieces,
                'piece_type': self.piece_type
            })
            self.weight_or_qty = 0
            self.local_price = 0 
            self.external_price = 0
        return True

    def create_order(self):
        total_pieces = sum(self.cart_ids.mapped('pieces_qty'))
        if self.pieces_qty != total_pieces:
            raise ValidationError("La cantidad de piezas detallada en el carrito debe ser igual a la cantidad de piezas descrita en los calculos")

        self.state = 'order'
        if self.name == 'Borrador':
            sequence_id = self.env.ref('cm_cargo_handling.sequence_tracking_bill')
            if sequence_id:
                self.name = sequence_id.next_by_id()

    def set_to_quote(self):
        state_type = self.env.context.get('state')
        if state_type:
            self.state = state_type

    def create_invoices(self):
        if not self.cart_ids:
            raise ValidationError("No hay nada en el carrito para facturar")

        journal_id = self.env['account.journal'].search([('code','=','INV')])


        self.move_id = self.env['account.move'].create({
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_user_id': self.user_id.id,
            'journal_id': journal_id.id,
            'invoice_date': (datetime.now() - timedelta(hours=6)).date(),
            'currency_id': self.external_currency_id.id,
            'state': 'draft',
            'name': 'Borrador',
            'internal_number': 'Borrador',
        })

        line_vals = {
            'product_id': self.product_id.id,
            'name': self.product_id.name,
            'account_id': self.product_id.property_account_income_id.id,
            'price_unit': self.total,
            'move_id': self.move_id.id,
            'tax_ids': [(6, 0, self.product_id.taxes_id.ids)]
        }
        self.env['account.move.line'].create(line_vals)
        if self.modality in ['counted','credit']:
            self.allow_create_guides = True

    def create_guides(self):
        if self.modality == 'counted' and self.payment_state != 'paid':
            raise ValidationError('Modalidad Contado: Debe realizar el pago de la factura antes de crear las guias')

        if not self.cart_ids:
            raise ValidationError("No hay nada agregado al carrito")

        total_pieces = sum(self.cart_ids.mapped('pieces_qty'))
        if self.pieces_qty != total_pieces:
            raise ValidationError("La cantidad de piezas detallada en el carrito debe ser igual a la cantidad de piezas descrita en los calculos")

        len_cart = len(self.cart_ids)
        cont = 1
        for line in self.cart_ids:
            vals = {
                'order_id': self.id,
                'cart_line_id': line.id,
                'origin_id': self.origin_id.id,
                'destination_id': self.destination_id.id,
                'sender_name': self.sender_id.name,
                'id_sender': self.id_sender,
                'sender_phone': self.sender_phone,
                'receiver_name': self.receiver_id.name,
                'id_receiver': self.id_receiver,
                'receiver_phone': self.receiver_phone,
                'content_description': self.content_description,
                'observations': self.observations,
                'weight': line.weight_or_qty,
                'modality': self.modality
            }
            if self.content_description_ids:
                vals.update({'content_description_ids': [(6, 0, self.content_description_ids.ids)]})

            if line.pieces_qty > 1:
                for piece in range(1, (line.pieces_qty + 1)):
                    vals.update({'name': f"{self.name}-{piece}"})
                    self.env['cargo.bill'].create(vals)
            else:
                if len_cart == 1:
                    vals.update({'name': self.name})
                else:
                    vals.update({'name': f"{self.name}-{cont}"})
                    cont += 1
                self.env['cargo.bill'].create(vals)

            if self.modality in ['counted','credit']:
                self.state = 'invoiced'

            self.created_guides = True

    def print_guides(self):
        data = {'order_id': self.id}
        return self.env.ref('cm_cargo_handling.action_guide_format').report_action(self, data=data)

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
    pieces_qty = fields.Integer(string="Piezas",default=1)
    piece_type = fields.Selection([('uniform','Uniforme'),('mix','Mixta')], string="Tipo de pieza")