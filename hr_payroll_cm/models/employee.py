from odoo import models


class Employee(models.Model):
    _inherit = 'hr.employee'

    def get_employee_no(self):
        for employee in self:
            employee.employee_no = employee.registration_number or employee.barcode or employee.pin or ''
