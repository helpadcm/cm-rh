from odoo import fields, models


class Contract(models.Model):
    _inherit = 'hr.contract'

    hours_per_week = fields.Float(
        string='Horas por Semana',
        help='Horas de trabajo por semana',
        tracking=True,
        default=44.0
        )

    def calculate_deductions(self, code):
        deduction_ids = self.env['hr.salary.attachment'].search([('employee_ids','in',[self.employee_id.id])])
        amount = 0
        if deduction_ids:
            for ded in deduction_ids:
                if ded.deduction_type_id.code == code:
                    amount = ded.monthly_amount
        return amount

    def calculate_dt_dc(self, code, payslip):
        return self.temporal_amount
