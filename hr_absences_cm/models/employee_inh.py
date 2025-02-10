from odoo import fields, models, api

class HrEmployeeInh(models.Model):
    _inherit = 'hr.employee'

    compensatory_hours = fields.Float(string="Horas compensatorios Disp.")
    compensatory_day = fields.Float(string="Eq. Dias", compute="calculate_days")
    compensatory_day_string = fields.Char(string="Equivalente Dias", compute="calculate_days")
    vacations_day = fields.Integer(string="Vacaciones Disp.")
    program_to_fly = fields.Integer(string="Programa a Volar Disp.")

    @api.depends('compensatory_hours')
    def calculate_days(self):
        for rec in self:
            if rec.compensatory_hours > 0:
                rec.compensatory_day =  rec.compensatory_hours / 8
                days = int(rec.compensatory_hours // 8)
                hours = rec.compensatory_hours % 8
                rec.compensatory_day_string = f"{days} dia(s) y {hours} hora(s)"
            else:
                rec.compensatory_day = 0
                rec.compensatory_day_string = ''

class employeePublicHRInh(models.Model):
    _inherit = 'hr.employee.public'

    compensatory_hours = fields.Float(string="Dias compensatorios Disp.")
    compensatory_day = fields.Float(string="Eq. Dias", compute="calculate_days")
    compensatory_day_string = fields.Char(string="Equivalente Dias", compute="calculate_days")
    vacations_day = fields.Integer(string="Vacaciones Disp.")
    program_to_fly = fields.Integer(string="Programa a Volar Disp.")

    @api.depends('compensatory_hours')
    def calculate_days(self):
        for rec in self:
            if rec.compensatory_hours > 0:
                rec.compensatory_day =  rec.compensatory_hours / 8
                days = int(rec.compensatory_hours // 8)
                hours = rec.compensatory_hours % 8
                rec.compensatory_day_string = f"{days} dias y {hours} horas"
            else:
                rec.compensatory_day = 0
                rec.compensatory_day_string = ''