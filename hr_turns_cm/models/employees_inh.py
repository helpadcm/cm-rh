from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    notify_validate_turns = fields.Boolean(string="Not. de Turnos Validados")

class employeePublicInh(models.Model):
    _inherit = 'hr.employee.public'

    notify_validate_turns = fields.Boolean(string="Not. de Turnos Validados")

class contractInh(models.Model):
    _inherit = 'hr.contract'

    weekend_hours = fields.Integer(string="Horas Fines de Semana",default=8)
