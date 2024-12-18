from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class workTeams(models.Model):
    _name = 'hr.work.teams'
    _description = 'Teams: Work teams'

    name = fields.Char('Name')
    leader_id = fields.Many2one('hr.employee',string="Lider de Equipo")
    responsible_id = fields.Many2one('hr.employee',string="Responsable de Equipo")
    members_ids = fields.Many2many('hr.employee',string="Miembros")

class optionsSchedule(models.Model):
    _name = 'hr.options.schedules'
    _description = 'Horarios: horarios disponibles para los turnos'

    name = fields.Char(string="Nombre")