# -*- coding: utf-8 -*-
from odoo import api, exceptions, models,fields, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

class fleet(models.Model):
    _name = 'aff.fleet'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Flota"

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Codigo")
    fleet_type = fields.Selection([('internal','Interno'),('external','Externo')],string="Tipo de flota")
    aircraft_ids = fields.One2many('aff.aircraf','fleet_id',string="Aeronaves")

class aircraft(models.Model):
    _name = "aff.aircraf"
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Aeronaves"
    _rec_name = "msn"

    fleet_id = fields.Many2one('aff.fleet',string="Flota")
    msn = fields.Char(string="MSN")
    tuition = fields.Char(string="Matricula")
    brand = fields.Char(string="Marca")
    seats_qty = fields.Integer(string="Cant. Asientos")
    year_of_manufacture = fields.Char(string="Año de fabricación")
    renewal_sequence = fields.Char(string="Secuencia de Renovacion")
    contract_type = fields.Selection([('dry','Dry'),('wet','Wet')],string="Tipo de Contrato")
    start_date = fields.Date(string="Fecha de Inicio")
    final_date = fields.Date(string="Fecha Final")
    months_duration = fields.Float(string="Duracion(Meses)", compute="duration_contract")

    @api.depends('start_date','final_date')
    def duration_contract(self):
        for rec in self:
            if rec.start_date and rec.final_date:
                rd = relativedelta(rec.final_date, rec.start_date)
                rec.months_duration = rd.years * 12 + rd.months
            else:
                rec.months_duration = 0