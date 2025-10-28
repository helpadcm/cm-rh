from odoo import models, fields, api

class departmentRRHHInh(models.Model):
    _inherit = 'hr.department'

    apply_ranking = fields.Boolean(string="Aplica a Ranking Puntualidad")

class employeeRRHHInh(models.Model):
    _inherit = 'hr.employee'

    template_id = fields.Many2one('hr.templates.turn',string="Plantilla de Horario")

class employeePublicRRHHInh(models.Model):
    _inherit = 'hr.employee.public'

    template_id = fields.Many2one('hr.templates.turn',string="Plantilla de Horario")