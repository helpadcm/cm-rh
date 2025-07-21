# -*- coding: utf-8 -*-
from odoo import api, exceptions, models, fields, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class CargoTypeSend(models.Model):
    _name = 'cargo.type'
    _description = "Tipo de Envio"

    name = fields.Char(string="Nombre")
    minim_weight = fields.Float(string="Peso Minimo")
    options = fields.Selection([('is_package', 'Paquete'), ('is_sobre', 'Sobre'), ('is_baggage', 'Equipaje'), ('is_saca', 'Saca')],string="Tipo")

class ContentDescription(models.Model):
    _name = 'cargo.content.description'
    _description = "Descripcion de contenido"

    name = fields.Char(string="Nombre")
    description = fields.Char(string="Descripcion")
    img_info = fields.Binary(string="Image tag")

class lostReason(models.Model):
    _name = 'handling.lost.reason'
    _description = "Motivos para desechar"
    _rec_names_search = ['name', 'code']

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Codigo")
    active = fields.Boolean(string="Activo", default=True)


class AdditionalServices(models.Model):
    _name = 'cargo.additional.services'
    _description = "Servicios Adicionales"

    description = fields.Char(string="Descripcion")
    name = fields.Char(string="Nombre")
    currency_id = fields.Many2one('res.currency', string='Moneda')
    type_service = fields.Selection([('fixed', 'Costo Fijo'), ('weight', 'Peso'), ('value', 'Valor'), ('rent', 'Renta'), ('date', 'Fecha')],string="Tipo de Servicio", required=True)
    by_weight = fields.Float(string="Por Peso")
    by_value = fields.Float(string="Por Valor")
    by_size = fields.Float(string="Por Tamaño")
    rent_product = fields.Many2one('cargo.rent.product', string="Producto")
    variable_factor = fields.Monetary(currency_field="currency_id", string="Variable factor")
    fixed_value = fields.Monetary(currency_field="currency_id", string="Valor Fijo")

class AdditionalServices(models.Model):
    _name = 'cargo.bill.additional.service'
    _description = "Servicios Adicionales en Factura"

    @api.depends('size_id', 'by_weight', 'weight', 'by_value', 'commercial_value', 'fixed_value')
    def _compute_total(self):
        for record in self:
            total = 0
            if record.type_service == "rent" and record.size_id:
                total += record.size_id.price
            if record.type_service == "weight":
                total += record.weight * record.by_weight
            if record.type_service == "value":
                total += record.commercial_value * record.by_value
            if record.type_service == "fixed":
                total += record.fixed_value
            record.total = total

    modality = fields.Selection([('upon_delivery', 'Por Cobrar'), ('credit', 'Credito'), ('counted', 'Contado'), ('conmail', '--NO USAR--')], string="Modalidad")
    description = fields.Char(string="Descripcion")
    name = fields.Char(string="Nombre")
    currency_id = fields.Many2one(related="additional_service.currency_id", string="Moneda")
    additional_service = fields.Many2one('cargo.additional.services', string="Seleccionar Servicio")
    type_service = fields.Selection(related="additional_service.type_service", string="Tipo de Servicio")
    weight = fields.Float(string="Peso")
    by_weight = fields.Float(string="Por Peso")
    by_value = fields.Float(string="Por Valor")
    by_size = fields.Float(string="Por Tamaño")
    date_send = fields.Date(string="Fecha de Envio")
    size_id = fields.Many2one('cargo.rent.product.size', string="Tamaño")
    commercial_value = fields.Monetary(currency_field="currency_id", string="Valor Comercial")
    order_id = fields.Many2one('sale.order.handling',string="Orden de Venta")
    bill_lading_id = fields.Many2one("cargo.bill", string="Guia de carga")
    # bill_lading_id_default = fields.Many2one("cargo.bill", string="Bill lading default")
    cargo_station_id = fields.Many2one("cargo.station", string="Aeropuerto")
    rent_product = fields.Many2one(related="additional_service.rent_product", string="Producto Alquilado")
    default = fields.Boolean("Por Defecto")
    variable_factor = fields.Monetary(currency_field="currency_id", string="Variable factor")
    fixed_value = fields.Monetary(related="additional_service.fixed_value", string="Valor Fijo")
    total = fields.Monetary(currency_field="currency_id", string="Total", compute='_compute_total')