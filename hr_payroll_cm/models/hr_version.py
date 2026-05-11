from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from collections import defaultdict
import pytz

class versionInh(models.Model):
    _inherit = 'hr.version'

    def calculate_deductions(self, code, payslip=False):
        amount = 0
        if code not in self.employee_id.skip_rules_ids.mapped('code'):
            if code in ['RAP','SSH']:
                amount = self.calculate_rap(code)
            else:
                deduction_ids = self.env['hr.salary.attachment'].search([('employee_ids','in',[self.employee_id.id]),('state','=','open'),('other_input_type_id.code','=',code)])
                if deduction_ids:
                    for ded in deduction_ids:
                        if ded.other_input_type_id.code == code:
                            payslip.salary_attachment_ids = [(4, ded.id)]
                            if not ded.by_quotes:
                                amount += ded.monthly_amount
                            else:
                                if not payslip:
                                    raise ValidationError(f"""Revise la configuracion de la regla salarial {code}""")

                                line_id = ded.payment_plan_ids.filtered(lambda plan: plan.date == payslip.date_from)
                                if line_id:
                                    amount += line_id.amount
                                    line_id.payslip_id = payslip.id
                                    line_id.state = 'paid'
        return amount

    def get_transport_bonus(self, payslip):
        domain = [('payslip_date_from','<=',payslip.date_from),('payslip_date_to','>=',payslip.date_to),('employee_id','=',self.employee_id.id),('state','=','finalized')]
        mark_ids = self.env['hr.employee.attendance.record'].search(domain)
        amount = 0
        if mark_ids:
            amount = sum(mark_ids.mapped('tb_pay'))
        return amount

    def calculate_basic(self,payslip):
        if payslip.worked_days_line_ids:
            work100_amount = sum(payslip.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id.code == 'WORK100').mapped('amount'))
            extras_amount = sum(payslip.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id.code != 'WORK100').mapped('amount'))
            if work100_amount == 0:
                work100_amount = self.wage
            amount = work100_amount + extras_amount
        else:
            amount = self.wage
        return amount


    def calculate_dt_dc(self, payslip):
        payslip_ids =  self.env['hr.payslip'].search([('date_to','>=',payslip.date_from),('date_to','<=',payslip.date_to),('employee_id','=',payslip.employee_id.id),('type_lot','=','normal')])
        basic_amount = 0
        extras = 0
        for slip in payslip_ids:
            if slip.worked_days_line_ids:
                extras += sum(slip.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id.code != 'WORK100').mapped('amount'))

            basic_salary_line_id = slip.line_ids.filtered(lambda line: line.salary_rule_id.code == 'BASIC')
            if basic_salary_line_id:
                basic_amount += basic_salary_line_id.total

        contract_actual = (self.wage * 2)
        total = contract_actual + basic_amount - extras
        return (total / 12)

    def calculate_rap(self, code):
        amount = 0
        if code not in self.employee_id.skip_rules_ids.mapped('code'):
            rap_id = self.env['hr.settings.rap'].search([])
            if len(rap_id) == 0:
                raise ValidationError("Debe crear las configuraciones de RAP antes")
            if code == 'RAP':
                percentage = (rap_id.percentage) / 100
                total_salary = self.wage * 2

                amount = ((total_salary - rap_id.min_salary) * percentage) / 2
            elif code == 'SSH':
                amount = rap_id.ihss_amount / 2

        return amount * -1