from odoo import fields, models, api
# import pymssql
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta, MO, SU
from pytz import timezone, utc
from collections import defaultdict
from odoo.tools.intervals import Intervals
from itertools import chain
import logging
import requests
import pytz

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    in_device_id = fields.Many2one(
        'hr.attendance.device',
        string='Device Check In',
        help='Device of the attendance.'
        )

    in_branch_id = fields.Many2one(
        'hr.branch',
        related='in_device_id.branch_id',
        string='Branch Check In',
        help='Branch of the attendance device.'
        )

    in_mode = fields.Selection(
        selection_add=[('attendance_system', 'Attendance System')], )

    out_device_id = fields.Many2one(
        'hr.attendance.device',
        string='Device Check Out',
        help='Device of the attendance.'
        )

    out_branch_id = fields.Many2one(
        'hr.branch',
        related='out_device_id.branch_id',
        string='Branch Check Out',
        help='Branch of the attendance device.'
        )

    out_mode = fields.Selection(
        selection_add=[('attendance_system', 'Attendance System')], )

    observations = fields.Char(string="Observaciones")

    attendance_date = fields.Date(string="Fecha de asistencia")

    def get_attendance_date(self):
        self.attendance_date = (self.check_in - timedelta(hours=6)).date()

    def connect_ws(self):
        last_date = datetime.now().date() - timedelta(days=1)
        clocks_ids = self.env['hr.attendance.device'].search([('device_active','=',True)])
        markings_values = []
        code_employees = []
        for clock in clocks_ids:
            # url = "http://10.1.4.56:8080/markings?ip_str=%s&port_str=%s&date=%s"%(str(clock.ip_address), str(clock.port), last_date)
            url = "http://181.115.21.90:9000/markings?ip_str=%s&port_str=%s&date=%s"%(str(clock.ip_address), str(clock.port), last_date)

            response = requests.get(url)
            if response.status_code == 200:
                markings = response.json()
                for each in markings:
                    atten_time = each.get('timestamp')
                    atten_time_dt = datetime.strptime(atten_time, "%Y-%m-%d %H:%M:%S") - timedelta(hours=6)
                    local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
                    local_dt = local_tz.localize(atten_time_dt, is_dst=None)
                    utc_dt = local_dt.astimezone(pytz.utc)
                    utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                    atten_time = datetime.strptime(utc_dt, "%Y-%m-%d %H:%M:%S")
                    atten_time = fields.Datetime.to_string(atten_time)
                    get_user_id = self.env['hr.employee'].search([('pin', '=', each.get('user_id'))])
                    if get_user_id:
                        vals = {
                            'date': atten_time_dt,
                            'code_clock': clock.id
                        }
                        if get_user_id.id in code_employees:
                            markings_values[code_employees.index(get_user_id.id)]['lines'].append(vals)
                        else:
                            code_employees.append(get_user_id.id)
                            markings_values.append({
                                'code_employee': get_user_id.pin,
                                'date': last_date,
                                'lines': [vals]
                            })
            else:
                print ("Error de conexion")

        if len(markings_values) > 0:
            self.create_real_marking(markings_values)

    # def connect_sql_server(self):
    #     server = '10.1.4.56'
    #     database = 'attendance'
    #     username = 'sa'
    #     password = "youStrong(@)Password"
    #     last_date = (datetime.now() - timedelta(days=1)).date()
    #     _logger = logging.getLogger(__name__)
    #     _logger.info("####################Intentando conexion######################")
    #     try:
    #         # Crear la conexión
    #         conn = pymssql.connect(
    #             server=server,
    #             user=username,
    #             password=password,
    #             database=database,
    #             port=1433
    #         )
    #         _logger.info("Conexión exitosa a SQL Server.")
    #         for cday in reversed(range(4)):
    #             check_date = datetime.now().date() - timedelta(days=cday)
    #             year = check_date.year
    #             month = check_date.month
    #             day = check_date.day

    #             query_sql = """SELECT usertable.NAME as employee,
    #                         checking.CHECKTIME as date,
    #                         DATENAME(WEEKDAY,checking.CHECKTIME) as day,
    #                         machine.MachineAlias as clock,
    #                         machine.MachineNumber as CODCLOCK,
    #                         usertable.SSN as codemployee
    #                     FROM CHECKINOUT as checking
    #                     INNER JOIN USERINFO as usertable ON checking.USERID = usertable.USERID
    #                     INNER JOIN Machines as machine ON checking.SENSORID = machine.MachineNumber
    #                     WHERE checking.CHECKTIME BETWEEN '%s-%s-%s 00:00:00' AND '%s-%s-%s 23:59:59'
    #                 """%(year,month,day,year,month,day)
                
    #             # Ejecutar una consulta de ejemplo
    #             cursor = conn.cursor()
    #             cursor.execute(query_sql)
    #             results = cursor.fetchall()
    #             code_employees = []
    #             markings = []
                
    #             for row in results:
    #                 code_emp = row[5]
    #                 date = row[1]
    #                 clock = row[4]
    #                 clock_id = self.env['hr.attendance.device'].search([('device_id','=',clock)])
    #                 if clock_id:
    #                     vals = {
    #                         'date': date,
    #                         'code_clock': clock
    #                     }
    #                     if code_emp in code_employees:
    #                         markings[code_employees.index(code_emp)]['lines'].append(vals)
    #                     else:
    #                         code_employees.append(code_emp)
    #                         markings.append({
    #                             'code_employee': code_emp,
    #                             'date': date,
    #                             'lines': [vals]
    #                         })

    #             # Cerrar conexión
    #             cursor.close()
    #             if markings:
    #                 self.create_real_marking(markings)
    #         conn.close()
    #     except Exception as e:
    #         _logger.info(f"Error al conectar a SQL Server: {e}")

    def create_real_marking(self, markings):
        for mark in markings:
            employee_id = self.env['hr.employee'].search([('pin','=',mark.get('code_employee'))])
            if employee_id:
                if len(mark.get('lines')) > 0:
                    real_marking_obj = self.env['real.marking.employees']
                    exist_marking_id = real_marking_obj.search([('employee_id','=',employee_id.id),('date','=',mark.get('date'))])
                    if not exist_marking_id:
                        real_marking_id = real_marking_obj.create({
                            'name': '%s %s'%(employee_id.name, mark.get('date')),
                            'employee_id': employee_id.id,
                            'date': mark.get('date')
                        })
                        for line in sorted(mark.get('lines'), key=lambda x: x['date']):
                            clock_id = self.env['hr.attendance.device'].search([('id','=',line.get('code_clock'))])
                            if clock_id:
                                self.env['list.marking.employees'].create({
                                    'marking_id': real_marking_id.id,
                                    'clock_id': clock_id.id,
                                    'date': line.get('date') + timedelta(hours=6)
                                })
                    else:
                        actual_marks = len(exist_marking_id.marking_ids)
                        consult_marks = len(mark.get('lines'))
                        for new_mark in mark.get('lines'):
                            new_mark_date = new_mark.get('date') + timedelta(hours=6)
                            mark_exist = exist_marking_id.marking_ids.filtered(lambda list_date: list_date.date == new_mark_date)
                            if len(mark_exist) == 0:
                                exist_marking_id.write({'state':'draft', 'lost_marking':True})
                                clock_id = self.env['hr.attendance.device'].search([('device_id','=',new_mark.get('code_clock'))])
                                if clock_id:
                                    self.env['list.marking.employees'].create({
                                        'marking_id': exist_marking_id.id,
                                        'clock_id': clock_id.id,
                                        'date': new_mark_date
                                    })


    def _update_overtime(self, attendance_domain=None):
        if not attendance_domain:
            attendance_domain = self._get_overtimes_to_update_domain()
        self.env['hr.attendance.overtime.line'].search(attendance_domain).unlink()
        all_attendances = (self | self.env['hr.attendance'].search(attendance_domain)).filtered_domain([('check_out', '!=', False)])
        if not all_attendances:
            return

        start_check_in = min(all_attendances.mapped('check_in')).date() - relativedelta(days=1)  # for timezone
        min_check_in = utc.localize(datetime.combine(start_check_in, datetime.min.time()))

        start_check_out = max(all_attendances.mapped('check_out')).date() + relativedelta(days=1)
        max_check_out = utc.localize(datetime.combine(start_check_out, datetime.max.time()))  # for timezone

        version_periods_by_employee = all_attendances.employee_id.sudo()._get_version_periods(min_check_in, max_check_out)
        attendances_by_employee = all_attendances.grouped('employee_id')
        attendances_by_ruleset = defaultdict(lambda: self.env['hr.attendance'])
        for employee, emp_attendance in attendances_by_employee.items():
            for attendance in emp_attendance:
                attendance_intervals = Intervals([(
                    utc.localize(attendance.check_in),
                    utc.localize(attendance.check_out),
                    self.env['hr.version'])])
                inter = Intervals(version_periods_by_employee[employee]) & attendance_intervals
                if not inter:
                    continue
                version = inter._items[0][2]
                ruleset = version.ruleset_id
                if ruleset:
                    attendances_by_ruleset[ruleset] += attendance
        employees = all_attendances.employee_id
        schedules_intervals_by_employee = employees._get_schedules_by_employee_by_work_type(min_check_in, max_check_out, version_periods_by_employee)
        overtime_vals_list = []
        for ruleset, ruleset_attendances in attendances_by_ruleset.items():
            attendances_dates = list(chain(*ruleset_attendances._get_dates().values()))
            overtime_vals_list.extend(
                ruleset.rule_ids._generate_overtime_vals_v2(min(attendances_dates), max(attendances_dates), ruleset_attendances, schedules_intervals_by_employee)
            )
        # self.env['hr.attendance.overtime.line'].create(overtime_vals_list)
        self.env.add_to_compute(self._fields['overtime_hours'], all_attendances)