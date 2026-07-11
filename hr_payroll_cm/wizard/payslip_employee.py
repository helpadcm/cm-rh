from odoo import models, fields, _, api
from babel.dates import format_date
import calendar
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class employeePayslipResume(models.TransientModel):
    _name = "hr.employee.payslip.resume"
    _description = "Resumen nominas por empleado"

    start_date = fields.Date('Fecha Inicial')
    end_date = fields.Date('Fecha Final')
    employee_id = fields.Many2one('hr.employee', string='Empleado')

    def print_report(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'employee_id': self.employee_id.id
        }
        return self.env.ref('hr_payroll_cm.action_employee_payslip_xlsx').report_action(self,data=data)