from odoo import fields, models, api

class HrEmployeeInh(models.Model):
    _inherit = 'hr.employee'

    compensatory_hours = fields.Float(string="Horas compensatorios Disp.")
    compensatory_day = fields.Float(string="Equivalente Dias", compute="calculate_days")
    vacations_day = fields.Integer(string="Vacaciones Disp.")
    program_to_fly = fields.Integer(string="Programa a Volar Disp.")

    @api.depends('compensatory_hours')
    def calculate_days(self):
        for rec in self:
            if rec.compensatory_hours > 0:
                rec.compensatory_day =  rec.compensatory_hours / 24
            else:
                rec.compensatory_day = 0

class employeePublicHRInh(models.Model):
    _inherit = 'hr.employee.public'

    compensatory_hours = fields.Float(string="Dias compensatorios Disp.")
    compensatory_day = fields.Float(string="Equivalente Dias", compute="calculate_days")
    vacations_day = fields.Integer(string="Vacaciones Disp.")
    program_to_fly = fields.Integer(string="Programa a Volar Disp.")

    @api.depends('compensatory_hours')
    def calculate_days(self):
        for rec in self:
            if rec.compensatory_hours > 0:
                rec.compensatory_day =  rec.compensatory_hours / 24
            else:
                rec.compensatory_day = 0