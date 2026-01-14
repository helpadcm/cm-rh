# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

states = [
    ('quote', 'Cotizacion'),
    ('order', 'Orden'),
    ('invoiced', 'Finalizado'),
    ('canceled', 'Cancelado')
]

class saleOrderHandling(models.Model):
    _name = 'sale.order.handling'
    _description = "Ordenes de venta encomiendas"
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = "name desc"

    @api.model
    def user_default(self):
        return self.env.user.id

    @api.model
    def default_client_rec(self):
        client_def_id = self.env['res.partner'].search([('default_client','=',True)])
        if client_def_id:
            return client_def_id.id

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


    name = fields.Char(string="Numero de orden", default="Borrador", tracking=True, copy=False)
    origin_id = fields.Many2one('cargo.station', string="Origen", default=origin_default, tracking=True)
    destination_id = fields.Many2one('cargo.station', string="Destino", tracking=True)
    user_id = fields.Many2one('res.users', string="Agente", default=user_default, tracking=True)
    product_id = fields.Many2one('product.product',string="Producto",tracking=True)
    udm_id = fields.Many2one('uom.uom',string="Udm")
    pricelist_id = fields.Many2one('pricelist.handling',string="Lista de Precio")
    date = fields.Datetime(string="Fecha de registro",default=default_date)
    local_currency_id = fields.Many2one('res.currency',string="Moneda Local")
    external_currency_id = fields.Many2one('res.currency',string="Moneda Extranjera")
    weight_or_qty = fields.Float(string="Cantidad", tracking=True, default=1)
    local_price = fields.Float(string="Precio Lps", compute="calculate_amounts", store=True)
    external_price = fields.Float(string="Precio USD", compute="calculate_amounts", store=True)
    tax_price = fields.Float(string="Impuestos USD", compute="calculate_amounts", store=True)
    total_amount_piece = fields.Float(string="Monto Total Pieza", compute="calculate_amounts", store=True)
    state = fields.Selection(states, string="Estado", default="quote", tracking=True)
    cart_ids = fields.One2many('cart.order.handling', 'order_id', string="Carrito de ordenes")
    listprice_domain = fields.Binary(string="Dominio de lista de precios", compute="update_pricelist")
    partner_id = fields.Many2one('res.partner',string="Cliente", tracking=True, default=default_client_rec)
    bill_lading_ids = fields.One2many('cargo.bill', 'order_id', string="Guias de Carga")
    has_contacts = fields.Boolean(string="Tiene contactos")
    content_description_ids = fields.Many2many('cargo.content.description', string="Descripcion del Contenido")
    apply_rtn = fields.Boolean(string="Agregar RTN",tracking=True)
    rtn = fields.Char(string="RTN",tracking=True)
    modality = fields.Selection([('upon_delivery','Por Cobrar'),('credit','Credito'),('counted','Contado')], string="Modalidad", default="counted",tracking=True)
    type_id = fields.Many2one(related="product_id.type_cargo",string="Tipo de carga",tracking=True)
    options	= fields.Selection(related="type_id.options", string="Tipo",tracking=True)
    content_description = fields.Text(string="Descripcion", tracking=True)
    observations = fields.Text(string="Observaciones", tracking=True)
    pieces_qty = fields.Integer(string="Piezas",default=1, tracking=True)
    piece_description = fields.Text(string="Descripcion Pieza", tracking=True)
    piece_type = fields.Selection([('uniform','Uniforme'),('mix','Mixta')], string="Tipo de pieza", tracking=True, default="mix")
    additional_services_ids = fields.One2many('cargo.bill.additional.service', 'order_id', string="Servicios Adicionales")
    qty_guides = fields.Integer(string="Cant. Guias", compute="calculate_total_guides")
    allow_create_guides = fields.Boolean(string="Crear guias?", copy=False)
    created_guides = fields.Boolean(string="Guias Creadas", copy=False)
    created_invoice = fields.Boolean(string="Factura Creada", copy=False)
    residual = fields.Monetary(string="Monto pendiente", currency_field='external_currency_id', related="move_id.amount_dffprepago")
    parent_id = fields.Many2one('res.partner',string="Fact. Autorizados",tracking=True)
    readonly_rtn = fields.Boolean(string="RTN solo lectura")
    default_client = fields.Boolean(string="Cliente por defecto")
    by_size = fields.Boolean(string="Por talla")
    options_size = fields.Selection([('little','Pequeño'),('big','Grande')], default='big', string="Talla",tracking=True)
    # Sender
    sender_id = fields.Many2one('res.partner.contact',string="Remitente", tracking=True)
    sender_name = fields.Char(string="Nombre Remitente", tracking=True)
    id_sender = fields.Char(string="Identidad Remitente", tracking=True)
    sender_phone = fields.Char(string="Telefono Remitente", tracking=True)
    # Receiver
    receiver_id = fields.Many2one('res.partner.contact',string="Destinatario", tracking=True)
    receiver_name = fields.Char(string="Nombre Destinatario", tracking=True)
    id_receiver = fields.Char(string="Identidad Destinatario", tracking=True)
    receiver_phone = fields.Char(string="Telefono Destinatario", tracking=True)

    weight = fields.Float(string="Peso LBS", compute="calculate_totals", store=True)
    weight_piece = fields.Float(string="Peso(LBS)",tracking=True)
    suitcase_weight = fields.Float(string="Peso en maleta",tracking=True)
    preliminar_price = fields.Float(string="Precio preliminar ($)", compute='calculate_totals', store=True)
    amount_tax = fields.Float(string="Isv", compute='calculate_totals', store=True)
    amount_untaxed = fields.Float(string="Base imponible", compute='calculate_totals', store=True)
    amount_total = fields.Float(string="Total", compute='calculate_totals', store=True)
    total = fields.Float(string="Subtotal", compute='calculate_totals', store=True,tracking=True)
    amount_total_lps = fields.Float(string="Total (Lps)", compute='calculate_totals', store=True)
    additional_costs = fields.Float(string="Costos Adicionales ($)", compute='calculate_totals',store=True)
    discount = fields.Float(string="Descuento", compute='calculate_totals',store=True)

    move_id = fields.Many2one('account.move',string="Factura", copy=False)
    payment_state = fields.Selection(string="Estado de Pago", related="move_id.prestate2")
    sum_points = fields.Boolean(string="Acumula puntos")
    client_name = fields.Char(string="Nombre del cliente",tracking=True)
    volumen = fields.Float(string="Volumen",tracking=True)
    volumen_list_id = fields.Many2one('cargo.volumen.list',string="Listado Volumetrico",tracking=True)
    uom_name = fields.Char(string="Nombre unidad de medida")
    discount_id = fields.Many2one('cargo.discount',string="Descuento")
    product_code = fields.Char(string="Codigo de producto")

    def action_desechar(self):
        for record in self:
            today = datetime.now()
            midnight_totay = today.replace(hour=0, minute=0, second=0, microsecond=0)
            
            if record.create_uid.id == self.env.user.id or self.env.user.has_group("cm_cargo_handling.group_desechar_guias"):
                if record.move_id.payment_state == "paid":
                    raise ValidationError("La Factura ya se encuentra Pagada")

                if record.move_id.payment_state == "partial":
                    raise ValidationError("La Factura ya tiene pagos de caja")

                guides_ids = self.env['cargo.bill'].search([('order_id','=',record.id)])
                val = {'default_guia_ids': [(6,0,guides_ids.ids)]}
                res = {
                    'type': 'ir.actions.act_window',
                    'name': _("Motivo de Desechar"),
                    'res_model': 'cm_cargo_handling.desechar_guia',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'context': val,
                    'target': 'new',
                    }

                return res
            else:
                raise ValidationError("Debe ser el usuario que creo la guia o tener el permiso para desechar todas la guias")

    @api.constrains('id_receiver','id_sender','rtn','sender_phone','receiver_phone')
    def _validate_dates(self):
        for rec in self:
            if rec.rtn:
                if len(rec.rtn) != 14:
                    raise ValidationError("El RTN debe contener 14 digitos")

            if rec.id_receiver:
                if not rec.id_receiver.isdigit():
                    raise ValidationError("El campo identidad debe contener solo valores numéricos.")

                if len(rec.id_receiver) < 5:
                    raise ValidationError("Los numeros de identidad deben tener minimo 10 digitos")

            if rec.id_sender:
                if not rec.id_sender.isdigit():
                    raise ValidationError("El campo identidad debe contener solo valores numéricos.")

                if len(rec.id_sender) < 5:
                    raise ValidationError("Los numeros de identidad deben tener minimo 10 digitos")

            if rec.sender_phone:
                if not rec.sender_phone.isdigit():
                    raise ValidationError("El campo telefono debe contener solo valores numéricos.")

            if rec.receiver_phone:
                if not rec.receiver_phone.isdigit():
                    raise ValidationError("El campo telefono debe contener solo valores numéricos.")

    @api.onchange('volumen_list_id')
    def _onchange_volumen_list_id(self):
        if self.volumen_list_id:
            self.volumen = self.volumen_list_id.volumen

    @api.onchange('modality', 'default_client','discount_id')
    def allow_create_handling(self):
        if self.modality == 'upon_delivery' or self.discount_id.code in ['COMAIL','G10']:
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
        for record in self:
            if record.modality == 'counted' and not record.move_id:
                record.create_invoices()

            if record.move_id.state == 'draft':
                record.move_id.action_post()

            val = {"default_partner_id":record.partner_id.id, 
                "default_invoice_id":record.move_id.id, 
                "default_user_id": self.env.user.id, 
                "default_communication": record.move_id.name, 
                'default_cargo_handling_id': record.id,
                'default_rtn': record.rtn,
                'default_client_name': record.client_name
            }

            res={
                'type': 'ir.actions.act_window',
                'name':_("Registrar Prepago"),
                'res_model': 'cm.prepago',
                'view_type': 'form',
                'view_mode':'form',
                'context':val,
                'target': 'new',
            }

            return res

    @api.depends('cart_ids')
    def calculate_total_guides(self):
        for rec in self:
            rec.qty_guides = sum(rec.cart_ids.mapped('pieces_qty'))

    @api.depends('cart_ids','product_id', 'origin_id', 'destination_id', 'modality', 'additional_services_ids','discount_id','partner_id')
    def calculate_totals(self):
        for rec in self:
            total_lbs = 0
            total_dls = 0
            additional_cost = 0
            total_included = 0
            total_volumen = 0
            total_discount = 0
            if rec.origin_id:
                if not rec.partner_id.no_credit:
                    additional_cost += rec.origin_id.internal_load_ori
            if rec.destination_id:
                if not rec.partner_id.no_credit:
                    additional_cost += rec.destination_id.internal_load_dest

            if rec.additional_services_ids:
                additional_cost += sum(rec.additional_services_ids.mapped('total'))

            if rec.modality in ['upon_delivery','credit']:
                if not rec.partner_id.no_credit:
                    additional_cost += 1

            rec.additional_costs = additional_cost

            for line in rec.cart_ids:
                total_lbs += line.weight_piece
                total_dls += line.external_price
                total_volumen += line.volumen
            
            subtotal = total_dls + additional_cost + total_volumen
            
            if rec.discount_id:
                discount_amount = 0
                if rec.discount_id:
                    line_id = rec.product_id.price_list_ids.filtered(lambda line: line.rute_id.origin_id.id == rec.origin_id.airport_id.id and line.rute_id.destination_id.id == rec.destination_id.airport_id.id)
                    if rec.discount_id.discount_by == 'weight':
                        total_discount = rec.discount_id.discount_weight * line_id.min_price
                    else:
                        total_discount = subtotal * (rec.discount_id.porcentage/100)
                    subtotal -= total_discount
            
            rec.weight = total_lbs
            rec.discount = total_discount
            rec.preliminar_price = total_dls + total_volumen

            if subtotal < 0:
                subtotal = 0
            rec.amount_untaxed = subtotal
            rec.total = subtotal

            taxes = rec.product_id.taxes_id.compute_all(subtotal, rec.external_currency_id, 1, product=rec.product_id, partner=False)
            if taxes:
                rec.amount_tax = round((taxes['total_included'] - taxes['total_excluded']), 2)
                total_included = taxes['total_included']
            
            rec.amount_total = total_included
            rec.amount_total_lps = rec.external_currency_id._convert(rec.amount_total, rec.local_currency_id, self.env.company, rec.date, True)


    @api.onchange('partner_id', 'parent_id')
    def show_contacts(self):
        vals_rtn = False
        if self.partner_id and not self.parent_id:
            if self.partner_id.default_client:
                self.has_contacts = False
                self.default_client = True
                self.apply_rtn = False
                self.modality = 'counted'
                self.readonly_rtn = False
            else:
                self.has_contacts = True
                self.apply_rtn = True
                self.client_name = self.partner_id.name
                vals_rtn = self.partner_id.vat
                self.modality = self.partner_id.modality
                self.discount_id = self.partner_id.discount_id.id

                if self.partner_id.modality == 'credit':
                    self.readonly_rtn = True
                else:
                    self.readonly_rtn = False

        if self.parent_id:
            vals_rtn = self.parent_id.vat
            self.client_name = self.parent_id.name
        self.rtn = vals_rtn
        self.product_id = self.partner_id.default_product_id.id
    
    @api.onchange('sender_id')
    def get_data_sender(self):
        if self.sender_id:
            self.id_sender = self.sender_id.identity
            self.sender_phone = self.sender_id.phone
            self.sender_name = self.sender_id.name

    @api.onchange('receiver_id')
    def get_data_receiver(self):
        if self.receiver_id:
            self.id_receiver = self.receiver_id.identity
            self.receiver_phone = self.receiver_id.phone
            self.receiver_name = self.receiver_id.name

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
            self.by_size = self.product_id.by_size
            self.uom_name = self.product_id.uom_id.name
            self.product_code = self.product_id.default_code

    @api.depends('product_id', 'pricelist_id', 'weight_or_qty', 'options_size', 'weight_piece', 'origin_id', 'destination_id', 'volumen', 'additional_costs', 'uom_name', 'discount_id')
    def calculate_amounts(self):
        for rec in self:
            if rec.product_id:
                line_id = False
                if not rec.pricelist_id:
                    line_id = rec.product_id.price_list_ids.filtered(lambda line: line.rute_id.origin_id.id == rec.origin_id.airport_id.id and line.rute_id.destination_id.id == rec.destination_id.airport_id.id)
                else:
                    line_id = rec.pricelist_id.list_product_ids.filtered(lambda line: line.product_id.id == rec.product_id.id)
                
                price = 0
                if rec.product_id.by_size:
                    if rec.options_size == 'little':
                        price = rec.product_id.little_amount
                    else:
                        price = rec.product_id.big_amount

                if line_id:
                    discount_amount = 0

                    if rec.weight_or_qty > 0 and rec.uom_name == 'Unidades':
                        if rec.weight_or_qty <= line_id.qty_min:
                            price += line_id.price
                        else:
                            price += line_id.min_price * rec.weight_or_qty
                    
                    if rec.weight_piece > 0 and rec.uom_name != 'Unidades':
                        if rec.weight_piece <= line_id.qty_min:
                            price += (line_id.price - discount_amount)
                        else:
                            price += ((line_id.min_price * rec.weight_piece) - discount_amount)

                elif not line_id and not rec.product_id.by_size:
                    raise ValidationError("No hay regla de precio para el producto seleccionado en la lista de precio")
                            
                if rec.volumen > 0:
                    price += rec.volumen

                if rec.additional_costs > 0:
                    price += rec.additional_costs

                taxes = rec.product_id.taxes_id.compute_all(price, rec.external_currency_id, 1, product=rec.product_id, partner=False)
                # tax_amount = price * 0.15
                tax_amount = round((taxes['total_included'] - taxes['total_excluded']), 2)
                rec.external_price = price
                rec.tax_price = tax_amount
                rec.total_amount_piece = price + tax_amount
                rec.local_price = rec.external_currency_id._convert((rec.total_amount_piece), rec.local_currency_id, self.env.company, rec.date, True)

    def add_cart(self):
        if self.cart_ids:
            total_qty = sum(self.cart_ids.mapped('pieces_qty'))
            cart_modality = self.cart_ids.mapped('product_id.modality')[0]

            if cart_modality != self.product_id.modality:
                raise ValidationError(f"El producto {self.product_id.name} no es combinable")

            if total_qty == self.pieces_qty:
                raise ValidationError("No puede agregar mas lineas al carrito, la cantidad de piezas no puede ser mayor")

        if self.weight_or_qty == 0 and self.weight_piece == 0:
            raise ValidationError("La cantidad debe ser mayor de cero")

        if not self.piece_description:
            raise ValidationError("Debe agregar una descripcion de la pieza a ingresar")

        if not self.product_id:
            raise ValidationError("Debe agregar un producto")

        if self.volumen != 0 and self.partner_id.no_volumen:
            raise ValidationError(f"""No puede agregar volumen para encomiendas del clientes {self.partner_id.name}""")

        if self.partner_id.default_product_id:
            if self.product_id.id != self.partner_id.default_product_id.id:
                raise ValidationError(f"""No puede agregar otro producto distinto a {self.partner_id.default_product_id.name} para el cliente {self.partner_id.name}""")

        if self.weight_or_qty > 0 or self.weight_piece > 0:
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
                'local_price': (self.local_price * pieces),
                'external_price': (self.external_price * pieces) - self.additional_costs - self.volumen,
                'partner_id': self.partner_id.id,
                'pieces_qty': pieces,
                'piece_description': self.piece_description,
                'piece_type': self.piece_type,
                'volumen': self.volumen,
                'weight_piece': self.weight_piece or self.suitcase_weight
            })
            self.weight_or_qty = 0
            self.weight_piece = 0
            self.volumen_list_id = False
            self.volumen = 0
            self.local_price = 0 
            self.external_price = 0
            self.tax_price = 0
            self.total_amount_piece = 0
        return True

    def create_order(self):
        if self.modality == 'credit':
            if self.partner_id.modality != 'credit':
                raise ValidationError("El cliente seleccionado no esta configurado como cliente de credito, si hay algun error comuniquese con el o la encargada de creditos")

            if self.partner_id.available_credit < self.amount_total:
                raise ValidationError(f"""El cliente {self.partner_id.name} no tiene credito disponible para esta orden. Su saldo actual es de {self.partner_id.available_credit}""")

        if self.partner_id.default_client and self.modality == 'credit':
            raise ValidationError("El cliente consumidor final no puede validarse con modalidad de credito")

        if not self.sender_id or not self.id_sender or not self.sender_phone:
            raise ValidationError("No ha ingresado los datos necesarios del remitente (Nombre, Identidad, Telefono)")

        if not self.receiver_id or not self.receiver_phone:
            raise ValidationError("No ha ingresado los datos necesarios del destinatario (Nombre, Telefono)")


        total_pieces = sum(self.cart_ids.mapped('pieces_qty'))
        if self.pieces_qty != total_pieces:
            raise ValidationError("La cantidad de piezas detallada en el carrito debe ser igual a la cantidad de piezas descrita en los calculos")

        self.state = 'order'
        if self.name == 'Borrador':
            sequence_id = self.env.ref('cm_cargo_handling.sequence_tracking_bill')
            if sequence_id:
                self.name = sequence_id.next_by_id()

        if self.sender_id:
            self.sender_id.phone = self.sender_phone
            self.sender_id.identity = self.id_sender
            self.sender_id.generate_code()

        if self.receiver_id:
            self.receiver_id.phone = self.receiver_phone
            self.receiver_id.identity = self.id_receiver
            self.receiver_id.generate_code()

    def set_to_quote(self):
        state_type = self.env.context.get('state')
        if state_type:
            self.state = state_type

    def add_order_invoice(self):
        for rec in self:
            if rec.move_id:
                rec.move_id.from_handling = True
                rec.move_id.order_handling_id = rec.id

    def create_invoices(self):
        if not self.cart_ids:
            raise ValidationError("No hay nada en el carrito para facturar")

        if not self.partner_id:
            raise ValidationError("No ha agregado cliente")

        journal_id = self.env['account.journal'].search([('code','=','INV')])

        invoice_partner_id = self.partner_id
        if self.parent_id:
            invoice_partner_id = self.parent_id

        self.move_id = self.env['account.move'].create({
            'partner_id': invoice_partner_id.id,
            'partner_name': self.client_name or invoice_partner_id.name,
            'rtn_name': self.rtn or invoice_partner_id.vat,
            'move_type': 'out_invoice',
            'order_handling_id': self.id,
            'invoice_user_id': self.user_id.id,
            'from_handling': True,
            'modality': self.modality,
            'journal_id': journal_id.id,
            'invoice_date': (datetime.now() - timedelta(hours=6)).date(),
            'currency_id': self.external_currency_id.id,
            'state': 'draft',
            'name': 'Borrador',
            'internal_number': 'Borrador',
        })

        line_vals = {
            'product_id': self.product_id.id,
            'partner_id': invoice_partner_id.id,
            'name': self.product_id.name,
            'account_id': self.product_id.property_account_income_id.id,
            'price_unit': self.total,
            'move_id': self.move_id.id,
            'tax_ids': [(6, 0, self.product_id.taxes_id.ids)]
        }
        self.env['account.move.line'].create(line_vals)

        if self.modality in ['counted','credit']:
            if self.modality == 'credit' and not self.created_invoice:
                self.move_id.action_post()
                self.with_context({"create": True}).create_guides()
            self.allow_create_guides = True

        self.created_invoice = True

    def create_guides(self):
        create = self.env.context.get('create')
        if not create:
            if self.modality == 'counted' and self.move_id.prestate2 != 'paid' and self.discount_id.code not in ['COMAIL','G10']:
                raise ValidationError('Modalidad Contado: Debe realizar el pago de la factura antes de crear las guias')

        if not self.cart_ids:
            raise ValidationError("No hay nada agregado al carrito")

        total_pieces = sum(self.cart_ids.mapped('pieces_qty'))
        if self.pieces_qty != total_pieces:
            raise ValidationError("La cantidad de piezas detallada en el carrito debe ser igual a la cantidad de piezas descrita en los calculos")

        if not self.partner_id:
            raise ValidationError("No ha agregado cliente")

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
                'content_description': line.piece_description,
                'observations': self.observations,
                'weight': line.weight_piece,
                'qty': line.weight_or_qty,
                'product_id': line.product_id.id,
                'modality': self.modality,
                'volumen': line.volumen,
                'amount_total': self.amount_total,
                'amount_total_lps': self.amount_total_lps

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
        data = {'order_id': self.id, 'print_guides': True}
        return self.env.ref('cm_cargo_handling.action_guide_format').report_action(self, data=data)

    def print_invoice(self):
        data = {
            'order_id': self.id,
            'print_guides': False
            }
        return self.env.ref('cm_cargo_handling.action_invoice_guide_format').report_action(self, data=data)

    def unlink(self):
        for rec in self:
            if rec.state != 'quote':
                raise ValidationError("Solo se pueden borrar ordenes en estado de cotizacion")
        res = super(saleOrderHandling, self).unlink()
        return res

    def delete_orders(self):
        draft_order_ids = self.search([('state','=','quote')])
        if draft_order_ids:
            draft_order_ids.unlink()

class orderCartHandling(models.Model):
    _name = 'cart.order.handling'
    _description = "Carrito de ordenes"

    product_id = fields.Many2one('product.product',string="Producto")
    udm_id = fields.Many2one('uom.uom',string="Udm")
    local_currency_id = fields.Many2one('res.currency',string="Moneda Local")
    external_currency_id = fields.Many2one('res.currency',string="Moneda Extranjera")
    weight_or_qty = fields.Float(string="Cantidad", help="En este campo se debe agregar el peso en lbs o la cantidad de unidades, esto de acuerdo al producto que se este seleccionando")
    weight_piece = fields.Float(string="Peso(LBS)")
    local_price = fields.Float(string="Precio Lps")
    external_price = fields.Float(string="Precio USD")
    order_id = fields.Many2one('sale.order.handling',string="Orden de Venta")
    partner_id = fields.Many2one('res.partner',string="Cliente")
    pieces_qty = fields.Integer(string="Piezas",default=1)
    piece_type = fields.Selection([('uniform','Uniforme'),('mix','Mixta')], string="Tipo de pieza")
    piece_description = fields.Text(string="Descripcion Pieza")
    volumen = fields.Float(string="Volumen")