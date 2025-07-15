# -*- coding: utf-8 -*-
from odoo import api, exceptions, models,fields, _
from datetime import datetime

class Airport(models.Model):
	_name = 'cargo.airport'
	_description = "CTIS"
	_rec_name='ref'

	ref = fields.Char(string="Codigo", required=True)
	city = fields.Char(string="Ciudad", required=True)
	name = fields.Char(string="Nombre")
	valid_destinations = fields.One2many("cargo.airport.airport.rel", "origin_id", string="Destinos Validos")

class AirportAirportRel(models.Model):
	_name = "cargo.airport.airport.rel"
	_description = "CTIPAIR"
	
	origin_id = fields.Many2one('cargo.airport', string='Origen', ondelete='cascade')
	destination_id = fields.Many2one('cargo.airport', string='Destino', ondelete='cascade')
	kilometers = fields.Float("Kilometros")
	calculation_ids	= fields.One2many('cargo.calculations_by_type','cargo_airport_rel_id', string='Calculos')
	name = fields.Char(string="Nombre Ruta")

	@api.onchange('origin_id','destination_id')
	def get_name_rute(self):
		if self.origin_id and self.destination_id:
			route_name = f"{self.origin_id.ref} - {self.destination_id.ref}" 
			self.name = route_name

class calculations_by_type(models.Model):
	_name = 'cargo.calculations_by_type'
	_description = "Tipos de calculo"

	minim_weight = fields.Float(string="Peso Minimo")
	cargo_airport_rel_id = fields.Many2one('cargo.airport.airport.rel', string='Relacion Aeropuerto')
	type_cargo = fields.Many2one('cargo.type', string='Tipo de Envio')
	options = fields.Selection(related="type_cargo.options", string="Tipo Envio")
	include_km = fields.Boolean(string='Incluir KM', help='This will multiply the km to the factor')	
	type = fields.Selection([('factor','Factor * Peso'),('fixed_value','Monto Fijo'),('weight_with_grace', 'Peso de regalia')], string='Tipo', help="Factor will multiply the factor to the weight")
	factor_amount =	fields.Float("Monto del Factor", digits=(12,4), default=0.006)
	factor_volumetric =	fields.Float("Factor Volumetrico", digits=(12,4), default=0.006, help='Activated if the type is package')
	fixed_amount = fields.Float("Monto Fijo", digits=(12,4))
	weight_with_grace =	fields.Float("Peso de regalia en lb", digits=(12,4))

	@api.onchange('type')
	def onchange_type(self):
		for val in self:
			if val.type == 'fixed_value':
				val.include_km = False

	_sql_constraints = [
            ('unique_options_cargo_airlid',
            'UNIQUE (cargo_airport_rel_id,type_cargo)',
            'El tipo debe ser unico por ruta' )
    ]