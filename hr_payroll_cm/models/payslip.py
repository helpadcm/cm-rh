import dateutil
import pytz

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from collections import defaultdict, Counter
from datetime import datetime, time
import calendar

class HrPayslipBonus(models.Model):
    _inherit = 'hr.payslip'

    paid_date = fields.Date(
        compute="_compute_paid_date",
        string="Close Date",
        help="The date on which the payment is made to the employee."
        )

    esperated_hours = fields.Integer(string="Horas Esperadas", compute="get_esperated_hours")

    @api.depends('date_from','date_to')
    def get_esperated_hours(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                total_days = calendar.monthrange(rec.date_from.year, rec.date_from.month)[1]
                if rec.date_from.day == 1:
                    if total_days == 31:
                        rec.esperated_hours = 104
                    elif total_days == 30:
                        rec.esperated_hours = 96
                    elif total_days == 28:
                        rec.esperated_hours = 80
                    elif total_days == 29:
                        rec.esperated_hours = 88
                elif rec.date_from.day == 16:
                    rec.esperated_hours = 96
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
            payable_extra_hours = min(total_extra_hours, payslip.contract_id.max_extra_hours)

            wage = payslip.contract_id.wage
            hourly_wage = payslip.contract_id.wage * 1.25 / (15 * 8)
            extra_hours_value = hourly_wage * payable_extra_hours

            default_time_type = payslip.contract_id.structure_type_id.default_work_entry_type_id
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
            max_bonus = payslip.contract_id.max_transportation_bonus
            bonus_rate = payslip.contract_id.value_bonus
            early_checkin_bonus_time = payslip.contract_id.early_checkin_bonus_time
            late_checkout_bonus_time = payslip.contract_id.late_checkout_bonus_time
            if not payslip.contract_id.value_bonus:
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
                "contract_id": payslip.contract_id.id,
                "payslip_id": payslip.id,
                "input_type_id": payslip.env['hr.payslip.input.type'].search([("code", "=", "TRANSBONUS")])[0].id,
                }
            self.env["hr.payslip.input"].create(input_line_values)


    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to')
    def _compute_worked_days_line_ids(self):
        res = super(HrPayslipBonus, self)._compute_worked_days_line_ids()
        for payslip in self:
            domain = [('payslip_date_from','<=',payslip.date_from),('payslip_date_to','>=',payslip.date_to),('employee_id','=',payslip.employee_id.id),('state','=','finalized')]
            mark_id = self.env['hr.employee.attendance.record'].search(domain)
            if mark_id:
                hours = 0
                if mark_id.real_eh_pay > 0:
                    hours = mark_id.real_eh_pay
                elif mark_id.eh_pay > 0:
                    hours = mark_id.eh_pay

                if hours > 0:
                    entry_work_id = self.env['hr.work.entry.type'].search([('code','=','OVERTIME')])
                    if not entry_work_id:
                        raise ValidationError('No existe entrada de trabajo con codigo OVERTIME para horas adicionales')
                    
                    self.env['hr.payslip.worked_days'].create({
                        'payslip_id': payslip.id,
                        'work_entry_type_id': entry_work_id.id,
                        'number_of_hours': hours
                    })
        return res

class workedDaysInh(models.Model):
    _inherit = 'hr.payslip.worked_days'

    @api.depends('is_paid', 'is_credit_time', 'number_of_hours', 'payslip_id', 'contract_id.wage', 'payslip_id.sum_worked_hours')
    def _compute_amount(self):
        for worked_days in self:
            if worked_days.payslip_id.edited or worked_days.payslip_id.state not in ['draft', 'verify']:
                continue
            if not worked_days.contract_id or worked_days.code == 'OUT' or worked_days.is_credit_time:
                worked_days.amount = 0
                continue
            if worked_days.payslip_id.wage_type == "hourly":
                worked_days.amount = worked_days.payslip_id.contract_id.hourly_wage * worked_days.number_of_hours if worked_days.is_paid else 0
            else:
                #worked_days.amount = worked_days.payslip_id.contract_id.contract_wage * worked_days.number_of_hours / (worked_days.payslip_id.sum_worked_hours or 1) if worked_days.is_paid else 0
                wage = worked_days.payslip_id.contract_id.contract_wage * 2
                hours_amount = (wage / 30 / 8) * 1.25
                worked_days.amount = hours_amount * worked_days.number_of_hours