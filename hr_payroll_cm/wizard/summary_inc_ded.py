from odoo import models, fields, _, api
from babel.dates import format_date
import calendar
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class summaryIncomesDeductions(models.TransientModel):
    _name = "incomes.dedutions.summary"
    _description = "Resumen ingresos y deduducciones"

    start_date = fields.Date('Fecha Inicial')
    end_date = fields.Date('Fecha Final')
    employee_ids = fields.Many2many('hr.employee', string='Empleado')
    incomes_rules = fields.Many2many('hr.salary.rule' ,string="Ingresos")
    deductions_rules = fields.Selection(string="Deducciones", selection=lambda self: self.get_deductions_options())
    print_rules = fields.Selection([('incomes','Solo Ingresos'),('deductions','Solo Deducciones'),('both','Ambos')],string="Reglas a imprimir", default="both")

    def print_report(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'employee_id': self.employee_id.id
        }
        return self.env.ref('hr_payroll_cm.action_employee_payslip_xlsx').report_action(self,data=data)

    def get_deductions_options(self):
        rule_ids = self.env['hr.salary.rule'].search([('category_id.code','=','DED')])
        options_name = set(rule_ids.mapped('name'))
        return [(opt, opt) for opt in options_name]