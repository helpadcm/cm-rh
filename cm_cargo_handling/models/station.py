# -*- coding: utf-8 -*-
from odoo import api, exceptions, models,fields, _
from datetime import datetime

class CargoStation(models.Model):
	_name = "cargo.station"
	_rec_name='ref'
	_description = "Estaciones de Venta"

	ref = fields.Char(string="Codigo", required=True)	
	active = fields.Boolean(string="Activo", default=True)
	name = fields.Char(string="Nombre")
	address = fields.Char(string="Direccion")
	address_send  = fields.Char(string="Dirección Entrega")
	additional_services = fields.One2many('cargo.bill.additional.service','cargo_station_id',string="Servicios Adicionales")
	airport_id = fields.Many2one("cargo.airport",string="CTI",required=True)
	use_discounts = fields.Boolean(string="Usar Descuentos")
	discount_ids = fields.One2many('cargo.station.discounts','cargo_station_id',string="Descuentos")
	internal_load_dest = fields.Float(string="Cargo Interno Destino")
	internal_load_ori = fields.Float(string="Cargo Interno Origen")
	boss_station_id = fields.Many2one('res.users',string="Jefe de estación")

class CargoStationDiscounts(models.Model):
	_name = "cargo.station.discounts"
	_description = "Descuentos en estaciones"

	_sql_constraints = [
            ('unique_station_product',
            'UNIQUE (cargo_station_id,product_id)',
            'El producto debe ser unico por estacion' )
    ]	

	cargo_station_id = fields.Many2one('cargo.station',string="Estacion de Venta")
	product_id = fields.Many2one('product.product',string="Producto")	
	discount = fields.Float(string="Descuento(%)")

class fareClasses(models.Model):
	_name = "fare.clases"
	_description = "Clases Tarifarias"

	name = fields.Char(string="Nombre")
	code = fields.Char(string="Codigo")