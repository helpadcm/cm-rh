from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from collections import defaultdict
import pytz

class Contract(models.Model):
    _inherit = 'hr.contract'

    # hours_per_week = fields.Float(
    #     string='Horas por Semana',
    #     help='Horas de trabajo por semana',
    #     tracking=True,
    #     default=44.0
    #     )

    check_type = fields.Selection([('mark','Marcaje'),('turn','Planificación')],string="Tipo de revision",default="turn")
    skip_rules_ids = fields.Many2many('hr.inc.ded.rules', string="Omitir reglas")
    historical_salaries_ids = fields.One2many('historical.salaries.contract','contract_id',string="Historial de salarios")
    monthly_wage = fields.Monetary(string="Salario Mensual", tracking=True)

    @api.onchange('monthly_wage','schedule_pay')
    def calculate_salary(self):
        if self.schedule_pay == 'semi-monthly':
            if self.monthly_wage > 0:
                self.wage = self.monthly_wage / 2

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

    def calculate_deductions(self, code, payslip=False):
        amount = 0
        if code not in self.skip_rules_ids.mapped('code'):
            if code in ['RAP','SSH']:
                amount = self.calculate_rap(code)
            else:
                deduction_ids = self.env['hr.salary.attachment'].search([('employee_ids','in',[self.employee_id.id]),('state','=','open'),('deduction_type_id.code','=',code)])
                if deduction_ids:
                    for ded in deduction_ids:
                        if ded.deduction_type_id.code == code:
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
        if code not in self.skip_rules_ids.mapped('code'):
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

    def _get_work_hours(self, date_from, date_to, domain=None):
        assert isinstance(date_from, datetime)
        assert isinstance(date_to, datetime)

        # First, found work entry that didn't exceed interval.
        work_entries = self.env['hr.work.entry']._read_group(
            self._get_work_hours_domain(date_from, date_to, domain=domain, inside=True),
            ['work_entry_type_id'],
            ['duration:sum']
        )
        work_data = defaultdict(int)
        work_data.update({work_entry_type.id: duration_sum for work_entry_type, duration_sum in work_entries if not work_entry_type.hide_in_payslip})
        self._preprocess_work_hours_data(work_data, date_from, date_to)

        # Second, find work entry that exceeds interval and compute right duration.
        work_entries = self.env['hr.work.entry'].search(self._get_work_hours_domain(date_from, date_to, domain=domain, inside=False))

        for work_entry in work_entries:
            date_start = max(date_from, work_entry.date_start)
            date_stop = min(date_to, work_entry.date_stop)
            if work_entry.work_entry_type_id.is_leave:
                contract = work_entry.contract_id
                calendar = contract.resource_calendar_id
                employee = contract.employee_id
                contract_data = employee._get_work_days_data_batch(
                    date_start, date_stop, compute_leaves=False, calendar=calendar
                )[employee.id]

                work_data[work_entry.work_entry_type_id.id] += contract_data.get('hours', 0)
            else:
                work_data[work_entry.work_entry_type_id.id] += work_entry._get_work_duration(date_start, date_stop)  # Number of hours
        return work_data

    def add_salarial_historical(self):
        last_date = (datetime.now() - timedelta(days=1)).date()
        vals = {
            'contract_id': self.id,
            'employee_id': self.employee_id.id,
            'amount': self.wage * 2,
        }
        if self.historical_salaries_ids:
            actual_date = datetime.now().date()

            line_id = self.historical_salaries_ids[len(self.historical_salaries_ids) - 1]

            vals.update({'start_date': line_id.end_date + timedelta(days=1), 'end_date': actual_date - timedelta(days=1)})
            self.env['historical.salaries.contract'].create(vals)
        else:
            vals.update({'start_date': self.date_start, 'end_date': last_date})
            self.env['historical.salaries.contract'].create(vals)

class historicalSalaries(models.Model):
    _name = "historical.salaries.contract"
    _description = "Historial de salarios por contrato"

    contract_id = fields.Many2one('hr.contract', string="Contrato")
    start_date = fields.Date(string="Fecha Inicial")
    end_date = fields.Date(string="Fecha Final")
    amount = fields.Float(string="Sueldo Anterior")
    employee_id = fields.Many2one('hr.employee',string="Empleado")

    @api.onchange('contract_id')
    def get_contract_data(self):
        if self.contract_id:
            self.employee_id = self.contract_id.employee_id.id

    @api.onchange('employee_id')
    def get_contract_data(self):
        if self.employee_id:
            self.contract_id = self.employee_id.contract_id.id

class workEntryTypeInh(models.Model):
    _inherit = 'hr.work.entry.type'

    hide_in_payslip = fields.Boolean(string="No mostrar en recibo de nomina")