from odoo import models, fields


class Employee(models.Model):
    _inherit = 'hr.employee'

    def get_employee_no(self):
        for employee in self:
            employee.employee_no = employee.registration_number or employee.barcode or employee.pin or ''

class departmentInherit(models.Model):
    _inherit = 'hr.department'

    calculate_hours = fields.Selection([('one','1 vez'),('two','2 veces')], string="Calculo Horas al Mes", default="two")