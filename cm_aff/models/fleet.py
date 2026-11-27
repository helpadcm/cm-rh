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

    fleet_id = fields.Many2one('aff.fleet',string="Flota", tracking=True)
    msn = fields.Char(string="MSN", tracking=True)
    tuition = fields.Char(string="Matricula", tracking=True)
    brand = fields.Char(string="Marca", tracking=True)
    seats_qty = fields.Integer(string="Cant. Asientos", tracking=True)
    year_of_manufacture = fields.Char(string="Año de fabricación", tracking=True)
    renewal_sequence = fields.Char(string="Secuencia de Renovacion", tracking=True)
    contract_type = fields.Selection([('dry','Dry'),('wet','Wet')],string="Tipo de Contrato", tracking=True)
    start_date = fields.Date(string="Fecha de Inicio", tracking=True)
    final_date = fields.Date(string="Fecha Final", tracking=True)
    months_duration = fields.Float(string="Duracion(Meses)", compute="duration_contract")

    value_1 = fields.Float(string="0.24:1 or lower", tracking=True)
    value_2 = fields.Float(string="0.25:1 or 0.49:1", tracking=True)
    value_3 = fields.Float(string="0.50:1 or 0.74:1", tracking=True)
    value_4 = fields.Float(string="0.75:1 or 0.99:1", tracking=True)
    value_5 = fields.Float(string="1.0:1 or higher", tracking=True)

    @api.depends('start_date','final_date')
    def duration_contract(self):
        for rec in self:
            if rec.start_date and rec.final_date:
                rd = relativedelta(rec.final_date, rec.start_date)
                rec.months_duration = rd.years * 12 + rd.months
            else:
                rec.months_duration = 0