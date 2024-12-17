from odoo import fields, models
from odoo.exceptions import ValidationError


class Contract(models.Model):
    _inherit = 'hr.contract'

    hours_per_week = fields.Float(
        string='Horas por Semana',
        help='Horas de trabajo por semana',
        tracking=True,
        default=44.0
        )

    def get_historical(self, code):
        for rec in self:
            if code != 'ALL':
                payslip_line_ids =  self.env['hr.payslip.line'].search([('employee_id','=',rec.employee_id.id),(('salary_rule_id.code','=',code))])
                for line in payslip_line_ids:
                    amount = line.total
                    if amount < 0:
                        amount = amount * -1

                    self.env['hr.historical.deductions'].create({
                        'name': line.salary_rule_id.name,
                        'payslip_id': line.slip_id.id,
                        'employee_id': line.slip_id.employee_id.id,
                        'start_date': line.slip_id.date_from,
                        'end_date': line.slip_id.date_to,
                        'code': line.salary_rule_id.code,
                        'amount': amount
                    })
            else:
                payslip_line_ids =  self.env['hr.payslip.line'].search([('employee_id','=',rec.employee_id.id),('category_id.code','=','DED'),('salary_rule_id.code','not in',['RAP','SSH','ISR'])])
                for line in payslip_line_ids:
                    amount = line.total
                    if amount < 0:
                        amount = amount * -1
                    self.env['hr.historical.deductions'].create({
                        'name': line.salary_rule_id.name,
                        'payslip_id': line.slip_id.id,
                        'employee_id': line.slip_id.employee_id.id,
                        'start_date': line.slip_id.date_from,
                        'end_date': line.slip_id.date_to,
                        'code': line.salary_rule_id.code,
                        'amount': amount
                    })

    def calculate_deductions(self, code):
        amount = 0
        if code == 'RAP':
            amount = self.calculate_rap()
        else:
            deduction_ids = self.env['hr.salary.attachment'].search([('employee_ids','in',[self.employee_id.id]),('state','=','open')])
            if deduction_ids:
                for ded in deduction_ids:
                    if ded.deduction_type_id.code == code:
                        amount = ded.monthly_amount
        return amount

    def calculate_dt_dc(self, code, payslip):
        return self.temporal_amount

    def calculate_rap(self):
        rap_id = self.env['hr.settings.rap'].search([])
        if len(rap_id) == 0:
            raise ValidationError("Debe crear las configuraciones de RAP antes")
        
        percentage = (rap_id.percentage) / 100
        total_salary = self.wage * 2

        amount = ((total_salary - rap_id.min_salary) * percentage) / 2
        return amount * -1

    def show_historical(self):
        historical_ids = self.env['hr.historical.deductions'].search([('employee_id','=',self.employee_id.id)])
        domain = [('id','in',historical_ids.ids)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Deducciones',
            'view_mode': 'tree',
            'res_model': 'hr.historical.deductions',
            'domain': domain,
            'target': 'current',
            'context': dict(self.env.context, search_default_name_group=1)
        }