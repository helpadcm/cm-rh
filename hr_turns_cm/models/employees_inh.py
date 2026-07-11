from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    notify_validate_turns = fields.Boolean(string="Not. de Turnos Validados")
    weekend_hours = fields.Integer(string="Horas Fines de Semana",default=8)

class employeePublicInh(models.Model):
    _inherit = 'hr.employee.public'

    notify_validate_turns = fields.Boolean(string="Not. de Turnos Validados")
    weekend_hours = fields.Integer(string="Horas Fines de Semana",default=8)
