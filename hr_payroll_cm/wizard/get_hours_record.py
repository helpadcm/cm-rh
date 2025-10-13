from odoo import models, fields, _, api
from babel.dates import format_date
import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

months = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

class getRecordHours(models.TransientModel):
    _name = "hr.hours.employees"
    _description = "Hours Record employees"

    date = fields.Date('Date', readonly=True, default=fields.Date.context_today)
    department_id = fields.Many2one('hr.department', string='Department')
    employee_ids = fields.Many2many('hr.employee', string='Employee')
    company_id = fields.Many2one('res.company', 'Company', readonly=True)

    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)

    payslip_date_from = fields.Date(_('Start Date Pasylip'))
    payslip_date_to = fields.Date(_('End Date Payslip'))

    @api.onchange('date_from','department_id')
    def get_payslips_date(self):
        if self.date_from:
            year = self.date_from.year
            month = self.date_from.month
            if self.date_from.day >= 26:
                if month == 12:
                    date_from_payslip = "%s-%s-%s"%(year + 1, '01', '01')
                    date_to_payslip = "%s-%s-%s"%(year + 1, '01', 15)
                else:
                    date_from_payslip = "%s-%s-%s"%(year, month + 1, '01')
                    date_to_payslip = "%s-%s-%s"%(year, month + 1, 15)
            elif self.date_from.day <= 26:
                _, num_days = calendar.monthrange(year, month)
                date_from_payslip = "%s-%s-%s"%(year, month, 16)
                date_to_payslip = "%s-%s-%s"%(year, month, num_days)
                if self.department_id:
                    if self.department_id.calculate_hours == 'one':
                        date_from_payslip = "%s-%s-%s"%(year, month+1, '01')
                        date_to_payslip = "%s-%s-%s"%(year, month+1, 15)
                        
            self.payslip_date_from = date_from_payslip
            self.payslip_date_to = date_to_payslip

    def get_records(self):
        employees = self.employee_ids
        if not self.employee_ids:
            attendances_ids = self.env['hr.attendance'].search([('attendance_date', '>=', self.date_from),('attendance_date', '<=', self.date_to)])
            employees = attendances_ids.mapped('employee_id')
        else:
            employees = self.employee_ids.ids

        if self.department_id:
            employees = self.env['hr.employee'].search([('department_id','=',self.department_id.id)])

        data_employee = []
        for employee_id in employees:
            if not self.employee_ids:
                id_employee = employee_id.id
            else:
                id_employee = employee_id

            employee_report = self.env['hr.attendance.employee.report'].create({
                'employee_id': id_employee,
                'date_from': self.date_from,
                'date_to': self.date_to,
            })

            contract_id = self.env['hr.contract'].search([('employee_id','=',id_employee)])
            # Utilizar los métodos del modelo abstracto para obtener y procesar los datos
            employee_attendances = employee_report.get_attendance()
            employee_attendance_data = employee_report.process_employee_attendance()

            emp_data = []
            header_data = employee_attendance_data['header']
            rows_data = employee_attendance_data['rows']
            esperated_hours = self.get_esperated_hours(self.payslip_date_from, self.payslip_date_to)
            name_rec = self.get_name_rec(self.payslip_date_from)

            rec_id = self.env['hr.employee.attendance.record'].create({
                'name': 'Registro de Asistencia %s %s'%(header_data.get('employee'), header_data.get('start_date')),
                'period': name_rec,
                'employee_id': header_data.get('employee_id'),
                'department_id': contract_id.employee_id.department_id.id,
                'code': header_data.get('employee_no'),
                'start_date': header_data.get('start_date'),
                'end_date': header_data.get('end_date'),
                'esperated_hours': esperated_hours,
                'eh_limit': contract_id.max_extra_hours,
                'tb_max': contract_id.max_transportation_bonus,
                'tb_bonus': contract_id.value_bonus,
                'tb_limit': contract_id.max_transportation_bonus * contract_id.value_bonus,
                'payslip_date_from': self.payslip_date_from,
                'payslip_date_to': self.payslip_date_to
            })

            for row in rows_data:
                vals = {
                    'attendance_rec_id': rec_id.id,
                    'date': row.get('date'),
                    'day': format_date(row.get("date"), "EEEE", locale="es"),
                    'check_in_1': row.get('check_in_1').strftime("%H:%M:%S") if row.get("check_in_1") else "",
                    'check_out_1': row.get('check_out_1').strftime("%H:%M:%S") if row.get("check_out_1") else "",
                    'check_in_2': row.get('check_in_2').strftime("%H:%M:%S") if row.get("check_in_2") else "",
                    'check_out_2': row.get('check_out_2').strftime("%H:%M:%S") if row.get("check_out_2") else "",
                    'check_in_3': row.get('check_in_3').strftime("%H:%M:%S") if row.get("check_in_3") else "",
                    'check_out_3': row.get('check_out_3').strftime("%H:%M:%S") if row.get("check_out_3") else "",
                    'total_hours': row.get('total_hours'),
                    'ordinary_hours': row.get('ordinary_hours'),
                    'extra_hours': row.get('extra_hours'),
                    'observations': row.get('observation'),
                    'bonus': row.get('transport_bonus'),
                    'check_type': contract_id.check_type
                }
                turn_line_id = self.env['hr.turn.registration'].search([('employee_id','=',id_employee),('date','=',row.get('date'))])
                if turn_line_id:
                    if turn_line_id.state == 'draft':
                        raise ValidationError('La fecha %s del empleado %s en el equipo %s no ha sido validada'%(turn_line_id.date, contract_id.employee_id.name, turn_line_id.team_id.name))

                    entry_date_1 = self.convert_format(row.get('date'), turn_line_id.schedule1_in_id)
                    out_date_1 = self.convert_format(row.get('date'), turn_line_id.schedule1_out_id)
                    entry_date_2 = self.convert_format(row.get('date'), turn_line_id.schedule2_in_id)
                    out_date_2 = self.convert_format(row.get('date'), turn_line_id.schedule2_out_id)


                    vals.update({
                        'schedule1_in_date': entry_date_1,
                        'schedule1_out_date': out_date_1,
                        'turn_type_a': turn_line_id.turn_type_a.id,
                        'schedule2_in_date': entry_date_2,
                        'schedule2_out_date': out_date_2,
                        'turn_type_b': turn_line_id.turn_type_b.id,
                        'turn_note': turn_line_id.note,
                        'total_hours': turn_line_id.ordinary_hours,
                        'ordinary_hours': turn_line_id.oh,
                        'extra_hours': turn_line_id.aditional_hours,
                    })

                    if turn_line_id.turn_type_a.id == turn_line_id.turn_type_b.id:
                        personal_action = False
                        if turn_line_id.turn_type_a.code == 'LID':
                            personal_action = 'free'
                        elif turn_line_id.turn_type_a.code == 'F':
                            personal_action = 'holiday'
                        elif turn_line_id.turn_type_a.code == 'INC':
                            personal_action = 'inc'
                        elif turn_line_id.turn_type_a.code == 'PER':
                            personal_action = 'special'
                        elif turn_line_id.turn_type_a.code == 'COM':
                            personal_action = 'comp'
                        elif turn_line_id.turn_type_a.code == 'VAC':
                            personal_action = 'vac'
                        elif turn_line_id.turn_type_a.code == 'CAP':
                            personal_action = 'cap'
                        elif turn_line_id.turn_type_a.code == 'FT':
                            personal_action = 'wh'
                        elif turn_line_id.turn_type_a.code == 'CUB':
                            personal_action = 'coe'

                        if personal_action:                        
                            vals.update({'personal_action': personal_action})

                min_hours = []
                max_hours = []
                if contract_id.check_type == 'mark':
                    bonus = 0
                    amount1 = 0
                    amount2 = 0
                    amount3 = 0
                    if vals.get('check_in_1'):
                        entry_hour = self.convert_timedelta(vals.get('check_in_1'))
                        entry_total_sec = entry_hour.total_seconds()/3600
                        min_hours.append(entry_total_sec)
                    
                    if vals.get('check_in_2'):
                        entry_hour = self.convert_timedelta(vals.get('check_in_2'))
                        entry_total_sec = entry_hour.total_seconds()/3600
                        min_hours.append(entry_total_sec)

                    if vals.get('check_in_3'):
                        entry_hour = self.convert_timedelta(vals.get('check_in_3'))
                        entry_total_sec = entry_hour.total_seconds()/3600
                        min_hours.append(entry_total_sec)
                    
                    if vals.get('check_out_1'):
                        exit_hour = self.convert_timedelta(vals.get('check_out_1'))
                        exit_total_sec = exit_hour.total_seconds()/3600
                        max_hours.append(exit_total_sec)

                    if vals.get('check_out_2'):
                        exit_hour = self.convert_timedelta(vals.get('check_out_2'))
                        exit_total_sec = exit_hour.total_seconds()/3600
                        max_hours.append(exit_total_sec)

                    if vals.get('check_out_3'):
                        exit_hour = self.convert_timedelta(vals.get('check_out_3'))
                        exit_total_sec = exit_hour.total_seconds()/3600
                        max_hours.append(exit_total_sec)

                    try:
                        hour_1 = self.convert_timedelta(vals.get('check_in_1'))
                        hour_2 = self.convert_timedelta(vals.get('check_out_1'))
                        diff = hour_2 - hour_1
                        amount1 = diff.total_seconds()/3600
                    except:
                        amount1 = 0

                    try:
                        hour_1 = self.convert_timedelta(vals.get('check_in_2'))
                        hour_2 = self.convert_timedelta(vals.get('check_out_2'))
                        diff = hour_2 - hour_1
                        amount2 = diff.total_seconds()/3600
                    except:
                        amount2 = 0

                    try:
                        hour_1 = self.convert_timedelta(vals.get('check_in_3'))
                        hour_2 = self.convert_timedelta(vals.get('check_out_3'))
                        diff = hour_2 - hour_1
                        amount3 = diff.total_seconds()/3600
                    except:
                        amount3 = 0

                    bonus = self.calculate_bonus(min_hours, max_hours, contract_id)

                    total_h = amount1 + amount2 + amount3
                    extra_hours = 0
                    oh = 0
                    if row.get('date').weekday() in [5,6]:
                        if total_h > 0:
                            oh = contract_id.weekend_hours
                            extra_hours = total_h - contract_id.weekend_hours

                        vals.update({
                            'ordinary_hours': oh,
                            'extra_hours': extra_hours
                        })
                    else:
                        if total_h > 0:
                            oh = 8
                            extra_hours = total_h - 8

                        vals.update({
                            'ordinary_hours': oh,
                            'extra_hours': extra_hours
                        })

                    
                    if turn_line_id.turn_type_a.code == 'FT' and turn_line_id.turn_type_b.code == 'FT':
                        if extra_hours > 0:
                            vals.update({'holiday_hours': oh, 'holiday_extra_hours': extra_hours, 'personal_action': 'wh'})
                        else:
                            vals.update({'holiday_hours': oh, 'personal_action': 'wh'})
    
                    vals.update({
                        'bonus': bonus,
                        'total_hours': total_h
                    })

                line_id = self.env['hr.employee.attendance.line'].create(vals)
                line_id.personal_action_change()
        return True

    def get_name_rec(self, date_from):
        name = ''
        if date_from.day == 1:
            name = 'Primera Quincena %s %s'%(months[date_from.month - 1], date_from.year)
        elif date_from.day == 16:
            name = 'Segunda Quincena %s %s'%(months[date_from.month - 1], date_from.year)
        return name


    def calculate_bonus(self, check1, check2, contract_id):
        bonus = 0
        if check1:
            if min(check1) < contract_id.early_checkin_bonus_time:
                bonus += contract_id.value_bonus
        if check2:
            if max(check2) > contract_id.late_checkout_bonus_time:
                bonus += contract_id.value_bonus
        return bonus

    def convert_timedelta(self, hour):
        h, m, s = map(int, hour.split(":"))
        return timedelta(hours=h, minutes=m, seconds=s)

    def convert_format(self, date, schedule_id):
        if not schedule_id.alphabetical and schedule_id.name != 'NA':
            date = datetime.combine(date, datetime.min.time())
            hours = float(schedule_id.name) // 100
            minutes = float(schedule_id.name) % 100
            if minutes == 50:
                minutes = 30
            elif minutes == 25:
                minutes = 15
            new_date = date + timedelta(hours=hours, minutes=minutes)
            return new_date.strftime("%H:%M:%S")
        else:
            return False

    def get_esperated_hours(self, date_from, date_to):
        date = date_from
        esperated_hours = 0
        if date_from.day == 1:
            min_date = (date - relativedelta(months=1)).replace(day=25)
            max_date = date.replace(day=10)
            diff = (max_date - min_date)
            esperated_hours = (diff.days - 3) * 8
        elif date_from.day == 16:
            min_date = date.replace(day=10)
            max_date = date.replace(day=25)
            diff = (max_date - min_date)
            esperated_hours = (diff.days - 3) * 8
        else:
            esperated_hours = 0
        return esperated_hours