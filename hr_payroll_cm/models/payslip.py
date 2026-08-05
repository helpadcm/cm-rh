import dateutil
import pytz
import calendar

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from collections import defaultdict, Counter
from datetime import datetime, time, timedelta

from odoo.tools.safe_eval import safe_eval, datetime as safe_eval_datetime, dateutil as safe_eval_dateutil

class HrPayslipBonus(models.Model):
    _inherit = 'hr.payslip'

    paid_date = fields.Date(
        compute="_compute_paid_date",
        string="Close Date",
        help="The date on which the payment is made to the employee."
        )

    esperated_hours = fields.Integer(string="Horas Esperadas", compute="get_esperated_hours")
    type_lot = fields.Selection([('normal','Normal'),('fourteenth','Decimo Cuarto Mes'),('thirteenth','Decimo Tercer Mes')], string="Tipo de lote", default="normal")

    @api.model_create_multi
    def create(self, vals):
        res = super(HrPayslipBonus, self).create(vals)
        for rec in res:
            rec.type_lot = rec.payslip_run_id.type_lot
        return res

    @api.depends('date_from','date_to')
    def get_esperated_hours(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                total_days = calendar.monthrange(rec.date_from.year, rec.date_from.month)[1]
                date = rec.date_from
                if rec.date_from.day == 1:
                    min_date = (date - relativedelta(months=1)).replace(day=25)
                    max_date = date.replace(day=10)
                    diff = (max_date - min_date)
                    rec.esperated_hours = (diff.days - 3) * 8
                elif rec.date_from.day == 16:
                    min_date = date.replace(day=10)
                    max_date = date.replace(day=25)
                    diff = (max_date - min_date)
                    rec.esperated_hours = (diff.days - 3) * 8
                else:
                    rec.esperated_hours = 0

    def _compute_paid_date(self):
        for payslip in self:
            payslip.paid_date = payslip.date_to

    def action_recalculate_eh_day_based_cm(self):
        """
        Recalculates the extra hours based on the day for each payslip in the current set.

        For each payslip, the function calculates the sum of worked hours, the number of days in the interval,
        the number of ordinary hours, the total number of extra hours, and the number of payable extra hours.
        It also calculates the wage, the hourly wage, and the value of the extra hours.

        The function then creates a list of dictionaries representing the worked day lines, which includes
        information such as the payslip id, work entry type id, amount, name, number of days, and number of hours.

        After creating the worked day lines, the function unlinks the current worked days in the payslip,
        writes that the payslip has been edited, and creates new worked days based on the worked day lines.

        Args:
            self: The current set of payslips.

        Returns:
            None
        """

        for payslip in self:
            sum_worked_hours = int(payslip.sum_worked_hours * 2) / 2
            num_days = (payslip.date_to - payslip.date_from).days + 1
            num_weeks = num_days // 7
            remaining_days = num_days % 7
            ordinary_hours = num_weeks * 44 + remaining_days * 8
            total_extra_hours = max(0, sum_worked_hours - ordinary_hours)
            payable_extra_hours = min(total_extra_hours, payslip.employee_id.max_extra_hours)

            wage = payslip.employee_id.wage
            hourly_wage = payslip.employee_id.wage * 1.25 / (15 * 8)
            extra_hours_value = hourly_wage * payable_extra_hours

            default_time_type = payslip.employee_id.structure_type_id.default_work_entry_type_id
            default_overtime_type = payslip.env['hr.work.entry.type'].search([('code', '=', 'OVERTIME125')])[0]

            worked_day_lines = [
                {
                    'payslip_id': payslip.id,
                    'work_entry_type_id': default_time_type.id,
                    'amount': wage,
                    'name': 'Tiempo Nominal',
                    'number_of_days': ordinary_hours / 8,
                    'number_of_hours': ordinary_hours
                    },
                {
                    'payslip_id': payslip.id,
                    'work_entry_type_id': default_overtime_type.id,
                    'amount': extra_hours_value,
                    'name': 'Horas Extras',
                    'number_of_days': (payable_extra_hours / 8),
                    'number_of_hours': payable_extra_hours
                    }
                ]

            payslip.worked_days_line_ids.unlink()
            payslip.write({'edited': True})

            self.env['hr.payslip.worked_days'].create(worked_day_lines)

    def _count_bonus_for_record(
            self, work_entry,
            early_checkin_bonus_time,
            late_checkout_bonus_time
            ):
        tegucigalpa_tz = dateutil.tz.gettz('America/Tegucigalpa')
        date_start = work_entry["date_start"].astimezone(tegucigalpa_tz)
        date_stop = work_entry["date_stop"].astimezone(tegucigalpa_tz)
        bonus_count = 0
        checkin_time = date_start.time().hour + date_start.time().minute / 60
        checkout_time = date_stop.time().hour + date_stop.time().minute / 60

        if checkin_time <= early_checkin_bonus_time:
            bonus_count += 1

        if checkout_time >= late_checkout_bonus_time:
            bonus_count += 1

        return bonus_count

    def _calculate_transport_bonus(
            self,
            work_entries,
            max_bonus,
            early_checkin_bonus_time,
            late_checkout_bonus_time
            ):
        bonus_count = 0
        for work_entry in work_entries:
            bonus_count += self._count_bonus_for_record(
                work_entry,
                early_checkin_bonus_time,
                late_checkout_bonus_time
                )
            if bonus_count >= max_bonus:
                break
        return min(bonus_count, max_bonus)

    def _get_employee_work_entries(
            self, employee_id,
            work_entries_start_date,
            work_entries_end_date
            ):
        work_entries = self.env['hr.work.entry'].search(
            [
                ("employee_id", "=", employee_id.id),
                ("active", "=", True),
                ("date_start", ">=", work_entries_start_date),
                ("date_start", "<=", work_entries_end_date),
                ]
            )
        return work_entries

    def action_calculate_transport_bonus_for_payslip(self):
        for payslip in self:
            employee_id = payslip.employee_id
            work_entries = self._get_employee_work_entries(employee_id, payslip.date_from, payslip.date_to)
            max_bonus = employee_id.max_transportation_bonus
            bonus_rate = employee_id.value_bonus
            early_checkin_bonus_time = employee_id.early_checkin_bonus_time
            late_checkout_bonus_time = employee_id.late_checkout_bonus_time
            if not employee_id.value_bonus:
                return
            transport_bonus_count = self._calculate_transport_bonus(
                work_entries,
                max_bonus,
                early_checkin_bonus_time,
                late_checkout_bonus_time,
                )
            if transport_bonus_count == 0:
                return
            input_line_values = {
                "name": f"Otorgados {transport_bonus_count} Bonos de Transporte",
                "code": "TRANSBONUS",
                "amount": transport_bonus_count * bonus_rate,
                "employee_id": employee_id.id,
                "payslip_id": payslip.id,
                "input_type_id": payslip.env['hr.payslip.input.type'].search([("code", "=", "TRANSBONUS")])[0].id,
                }
            self.env["hr.payslip.input"].create(input_line_values)


    @api.depends('employee_id', 'version_id', 'struct_id', 'date_from', 'date_to')
    def _compute_worked_days_line_ids(self):
        res = super(HrPayslipBonus, self)._compute_worked_days_line_ids()
        valid_slips = self.filtered(lambda p: p.employee_id and p.date_from and p.date_to and p.struct_id)
        if not valid_slips:
            return
        
        for payslip in valid_slips:
            domain = [('payslip_date_from','<=',payslip.date_from),('payslip_date_to','>=',payslip.date_to),('employee_id','=',payslip.employee_id.id),('state','=','finalized')]
            mark_id = self.env['hr.employee.attendance.record'].search(domain)
            if mark_id and payslip:
                hours = mark_id.pay_extra_hours

                if hours > 0:
                    entry_work_id = self.env['hr.work.entry.type'].search([('code','=','OVERTIME')])
                    if not entry_work_id:
                        raise ValidationError('No existe entrada de trabajo con codigo OVERTIME para horas adicionales')
                    
                    values = {
                        'work_entry_type_id': entry_work_id.id,
                        'number_of_hours': hours,
                        'from_entry_register': True
                    }
                    payslip.update({'worked_days_line_ids': [(0, 0, values)]})
        return res

    def compute_sheet(self):
        for rec in self:
            rec.get_other_incomes()
        res = super(HrPayslipBonus, self).compute_sheet()
        for line in self.line_ids:
            if line.total == 0:
                line.unlink()
        return res

    # def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
    #     res =  super(HrPayslipBonus, self)._get_worked_day_lines(domain=None, check_out_of_contract=True)
    #     return res

    def get_other_incomes(self):
        deduction_lines_ids = self.input_line_ids.filtered(lambda line: line.input_type_id.entry_type == 'deduction')
        if deduction_lines_ids:
            deduction_lines_ids.unlink()

        obj_payslip_input = self.env['hr.payslip.input']
        vals = {
            'payslip_id': self.id
        }

        income_ids = self.env['hr.other.incomes'].search([('employee_id','=',self.employee_id.id),('state','=','in_progress')])
        if income_ids:
            if self.input_line_ids:
                incomes = income_ids.mapped('input_type_id').ids
                inc_line_ids = self.input_line_ids.filtered(lambda line: line.input_type_id.id in incomes)
                if inc_line_ids:
                    inc_line_ids.unlink()

            for income in income_ids:
                vals.update({
                    'input_type_id': income.input_type_id.id,
                    'name': income.name
                })
                if not income.by_quotes:
                    income.payslip_id = self.id
                    vals.update({'amount': income.amount})
                else:
                    line_id = income.payment_plan_ids.filtered(lambda plan: plan.date == self.date_from)
                    if line_id:
                        vals.update({'amount': line_id.amount})
                        line_id.payslip_id = self.id
                obj_payslip_input.create(vals)

        domain = [('payslip_date_from','<=',self.date_from),('payslip_date_to','>=',self.date_to),('employee_id','=',self.employee_id.id),('state','=','finalized')]
        mark_ids = self.env['hr.employee.attendance.record'].search(domain)
        if mark_ids:
            eh_amount = sum(mark_ids.mapped('eh_holiday'))
            ehx_amount = sum(mark_ids.mapped('eh_holiday_extra'))
            wage = self.employee_id.contract_wage * 2
            if eh_amount > 0:
                eh_type_id = self.env['hr.payslip.input.type'].search([('code','=','HF')])
                if eh_type_id:
                    hours_amount = (wage / 30 / 8)
                    amount = hours_amount * eh_amount
                    vals.update({
                        'input_type_id': eh_type_id.id,
                        'amount': amount,
                        'name': "%s (%s horas)"%(eh_type_id.name, eh_amount)
                    })
                    if self.input_line_ids:
                        hf_line_id = self.input_line_ids.filtered(lambda line: line.input_type_id.id == eh_type_id.id)
                        if hf_line_id:
                            hf_line_id.amount = amount
                        else:
                            obj_payslip_input.create(vals)
                    else:
                        obj_payslip_input.create(vals)

            if ehx_amount > 0:
                ehx_type_id = self.env['hr.payslip.input.type'].search([('code','=','HEF')])
                if ehx_type_id:
                    hours_amount = (wage / 30 / 8) * 1.25
                    amount = hours_amount * ehx_amount
                    vals.update({
                        'input_type_id': ehx_type_id.id,
                        'amount': amount,
                        'name': "%s (%s horas)"%(ehx_type_id.name, ehx_amount) 
                    })
                    if self.input_line_ids:
                        hef_line_id = self.input_line_ids.filtered(lambda line: line.input_type_id.id == ehx_type_id.id)
                        if hef_line_id:
                            hef_line_id.amount = amount
                        else:
                            obj_payslip_input.create(vals)
                    else:
                        obj_payslip_input.create(vals)

    def _action_create_account_move(self):
        return True

    def _generate_pdf(self):
        mapped_reports = self._get_pdf_reports()
        attachments_vals_list = []
        generic_name = _("Payslip")
        for report, payslips in mapped_reports.items():
            for payslip in payslips:
                pdf_content, dummy = self.env['ir.actions.report'].sudo().with_context(lang=payslip.employee_id.lang or self.env.lang)._render_qweb_pdf(report, payslip.id)
                if report.print_report_name:
                    pdf_name = safe_eval(report.print_report_name, {'object': payslip})
                else:
                    pdf_name = generic_name
                attachments_vals_list.append({
                    'name': pdf_name,
                    'type': 'binary',
                    'raw': pdf_content,
                    'res_model': payslip._name,
                    'res_id': payslip.id
                })

        self.env['ir.attachment'].sudo().create(attachments_vals_list)
        # Send email to employees (after attachment is created to include it in the mail by other bridge module)
        for payslips in mapped_reports.values():
            for payslip in payslips:
                template = payslip._get_email_template()
                # if template and payslip._check_send_payslip_mail():
                #     template.send_mail(payslip.id, email_layout_xmlid='mail.mail_notification_light')
                return True

class workedDaysInh(models.Model):
    _inherit = 'hr.payslip.worked_days'

    from_entry_register = fields.Boolean(string="Desde registro de entradas")

    @api.depends(
        'is_paid', 'number_of_hours', 'payslip_id', 'version_id.wage', 'version_id.hourly_wage', 'payslip_id.sum_worked_hours',
        'work_entry_type_id.amount_rate', 'work_entry_type_id.is_extra_hours')
    def _compute_amount(self):
        for worked_days in self:
            if worked_days.payslip_id.edited or worked_days.payslip_id.state != 'draft':
                continue
            if not worked_days.version_id or worked_days.code == 'OUT':
                worked_days.amount = 0
                continue
            version = worked_days.payslip_id.version_id
            amount_rate = worked_days.work_entry_type_id.amount_rate
            amount_days = 0
            if worked_days.payslip_id.wage_type == "hourly":
                hourly_rate = version.hourly_wage
                amount_days = hourly_rate * worked_days.number_of_hours * amount_rate if worked_days.is_paid else 0
            else:
                employee_id = worked_days.payslip_id.employee_id
                if worked_days.work_entry_type_id.code == 'OVERTIME':
                    wage = employee_id.contract_wage * 2
                    hours_amount = (wage / 30 / 8) * 1.25
                    amount_days = hours_amount * worked_days.number_of_hours

                elif worked_days.work_entry_type_id.code == 'WORK100':
                    before_diff = 0
                    after_diff = 0
                    if employee_id.contract_date_start > worked_days.payslip_id.date_from:
                        before_diff = (worked_days.payslip_id.date_to - employee_id.contract_date_start).days

                    if employee_id.contract_date_end and employee_id.contract_date_end < worked_days.payslip_id.date_to:
                        after_diff = (employee_id.contract_date_end - worked_days.payslip_id.date_from).days

                    diff_total = before_diff + after_diff
                    amount = employee_id.wage
                    day_amount = employee_id.wage/15
                    diff_days_amount = 0
                    if diff_total > 0:
                        diff_days_amount = day_amount * diff_total
                        amount_days = diff_days_amount
                    else:
                        amount_days = employee_id.contract_wage
                else:
                    attendance_hours = sum(
                        wd.number_of_hours for wd in worked_days.payslip_id.worked_days_line_ids
                        if not wd.work_entry_type_id.is_extra_hours
                    ) or 1
                    hourly_rate = version.contract_wage / attendance_hours
                    amount_days = hourly_rate * worked_days.number_of_hours * amount_rate if worked_days.is_paid else 0
            worked_days.amount = amount_days

class payslipLineInh(models.Model):
    _inherit = 'hr.payslip.line'

    deduction_id = fields.Many2one('hr.salary.attachment',string="Deduccion")