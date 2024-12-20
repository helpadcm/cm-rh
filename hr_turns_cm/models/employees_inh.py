from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    notify_validate_turns = fields.Boolean(string="Not. de Turnos Validados")

class employeePublicInh(models.Model):
    _inherit = 'hr.employee.public'

    notify_validate_turns = fields.Boolean(string="Not. de Turnos Validados")
