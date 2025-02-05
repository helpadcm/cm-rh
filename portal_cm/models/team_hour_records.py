from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

week_days = ['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo']

class teamHourRecord(models.Model):
    _name = 'team.hour.record'
    _description = 'Registro de Horas: Horas reales ingresadas por empleado'

    @api.model
    def _get_default_type(self):
        type_id =  self.env['hr.turn.types'].search([('default_turn','=',True)])
        return type_id.id

    name = fields.Char(string='Nombre')
    leader_id = fields.Many2one('hr.employee',string="Lider de Equipo")
    responsible_id = fields.Many2one('hr.employee',string="Responsable de Equipo")
    employee_id = fields.Many2one('hr.employee',string="Empleado")
    date = fields.Date(string="Fecha")
    name_day = fields.Char(string="Dia", compute="get_day_name")
    team_id = fields.Many2one('hr.work.teams',string="Equipo")
    schedule1_in_id = fields.Many2one('hr.options.schedules',string="Entrada 1")
    schedule1_out_id = fields.Many2one('hr.options.schedules',string="Salida 1")
    turn_type_a = fields.Many2one('hr.turn.types',string="Tipo Turno A", default=_get_default_type)
    schedule2_in_id = fields.Many2one('hr.options.schedules',string="Entrada 2")
    schedule2_out_id = fields.Many2one('hr.options.schedules',string="Salida 2")
    turn_type_b = fields.Many2one('hr.turn.types',string="Tipo Turno B", default=_get_default_type)
    ordinary_hours = fields.Float(string="Horas Totales")
    oh = fields.Float(string="HO")
    aditional_hours = fields.Float(string="Tiempo adicional")
    state = fields.Selection([('draft','Borrador'),('validated','Validado')],string="Estado",default='draft')
    editable_a = fields.Boolean(string="Editable A",default=True)
    editable_b = fields.Boolean(string="Editable B",default=True)
    note = fields.Text(string="Notas")

    @api.depends('date')
    def get_day_name(self):
        for rec in self:
            if rec.date:
                rec.name_day = week_days[rec.date.weekday()]
            else:
                rec.name_day = ''

    @api.onchange('turn_type_a')
    def send_values_a_turn(self):
        turn_na_id = self.env['hr.options.schedules'].search([('name','=','NA')])
        if self.turn_type_a.opt_turn == '0':
            self.schedule1_in_id = turn_na_id.id
            self.schedule1_out_id = turn_na_id.id
            self.editable_a = False
        return True

    @api.onchange('turn_type_b')
    def send_values_b_turn(self):
        turn_na_id = self.env['hr.options.schedules'].search([('name','=','NA')])
        if self.turn_type_b.opt_turn == '0':
            self.schedule2_in_id = turn_na_id.id
            self.schedule2_out_id = turn_na_id.id
            self.editable_b = False
        return True

    @api.onchange('schedule1_in_id','schedule1_out_id','schedule2_in_id','schedule2_out_id')
    def calculate_data(self):
        for rec in self:
            amount1 = 0
            amount2 = 0
            aditional1 = 4
            aditional2 = 4
            day = rec.date.weekday()
            try:
                amount1 = float(rec.schedule1_out_id.name) - float(rec.schedule1_in_id.name)
            except:
                amount1 = 0
                aditional1 = 0

            try:
                amount2 = float(rec.schedule2_out_id.name) - float(rec.schedule2_in_id.name)
            except:
                amount2 = 0
                aditional2 = 0

            rec.ordinary_hours = (amount1 + amount2) / 100
            if rec.ordinary_hours > 0:
                contract_id = rec.employee_id.sudo().contract_id
                if rec.date.weekday() in [5,6]:
                    rec.oh = rec.employee_id.contract_id.sudo().weekend_hours
                else:
                    rec.oh = 8
                rec.aditional_hours = rec.ordinary_hours - rec.oh
            elif rec.ordinary_hours == 0:
                rec.aditional_hours = 0