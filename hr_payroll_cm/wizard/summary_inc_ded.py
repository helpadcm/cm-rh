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
    show_details = fields.Boolean(string="Ver Detalles")
    incomes_rules = fields.Many2many(
        'hr.inc.ded.rules',
        'incomes_summary_rel',       # nombre único para la tabla relacional
        'summary_id', 'rule_id',
        string="Ingresos"
    )

    deductions_rules = fields.Many2many(
        'hr.inc.ded.rules',
        'deductions_summary_rel',    # otro nombre único para esta relación
        'summary_id', 'rule_id',
        string="Deducciones"
    )

    def print_report(self):
        if not self.incomes_rules and not self.deductions_rules:
            raise ValidationError("Debe seleccionar al menos un ingreso o una deduccion para imprimir")

        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'show_details': self.show_details,
            'employee_ids': self.employee_ids.ids,
            'incomes_rules': self.incomes_rules.mapped('code'),
            'deductions_rules': self.deductions_rules.mapped('code'),
        }
        return self.env.ref('hr_payroll_cm.action_inc_ded_payslip_xlsx').report_action(self,data=data)