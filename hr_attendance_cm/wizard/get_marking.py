# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta
import pymssql
import logging
from odoo.exceptions import UserError, ValidationError
import pytz
_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")

class getMarkings(models.TransientModel):
    _name = 'hr.get.markings'
    _description = "Obtener Marcajes de reloj"

    date = fields.Date(string="Fecha")
    employee_id = fields.Many2one('hr.employee',string="Empleado")
    option_form = fields.Selection([('db','A base de datos'),('clocks','A relojes')],string="Forma de obtener info",default="clocks")    

    def get_info_options(self):
        if self.option_form == 'db':
            self.connect_sql_server()
        else:
            self.connect_clocks()


    def connect_clocks(self):
        machines = self.env['hr.attendance.device'].search([('device_active','=',True)])
        for machine in machines:
            machine_ip = machine.ip_address
            zk_port = machine.port
            try:
                # Connecting with the device with the ip and port provided
                zk = ZK(machine_ip, port=zk_port, timeout=15,
                        password=0,
                        force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            self.action_set_timezone(machine)
            code_employees = []
            markings = []
            if conn:
                conn.disable_device()  # Device Cannot be used during this time.
                if self.employee_id:
                    user_id_to_find = self.employee_id.pin
                    user = [next((u for u in conn.get_users() if u.user_id == user_id_to_find), None)]
                else:
                    user = conn.get_users()
                attendance = conn.get_attendance()
                attendance_filter = filter(lambda a: a.timestamp.date() == self.date, attendance)
                if attendance_filter:
                    for each in attendance_filter:
                        atten_time = each.timestamp
                        local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
                        local_dt = local_tz.localize(atten_time, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                        atten_time = datetime.strptime(utc_dt, "%Y-%m-%d %H:%M:%S")
                        atten_time = fields.Datetime.to_string(atten_time)
                        for uid in user:
                            if uid.user_id == each.user_id:
                                get_user_id = self.env['hr.employee'].search([('pin', '=', each.user_id)])
                                if get_user_id:
                                    vals = {
                                        'date': each.timestamp,
                                        'code_clock': machine.device_id
                                    }
                                    if get_user_id.id in code_employees:
                                        markings[code_employees.index(get_user_id.id)]['lines'].append(vals)
                                    else:
                                        code_employees.append(get_user_id.id)
                                        markings.append({
                                            'code_employee': get_user_id.pin,
                                            'date': self.date,
                                            'lines': [vals]
                                        })
            self.create_real_marking(markings, self.option_form)

    def connect_sql_server(self):
        server = '10.1.4.56'
        database = 'attendance'
        username = 'sa'
        password = "youStrong(@)Password"
        _logger = logging.getLogger(__name__)
        _logger.info("####################Intentando conexion######################")
        try:
            # Crear la conexión
            conn = pymssql.connect(
                server=server,
                user=username,
                password=password,
                database=database,
                port=1433
            )
            _logger.info("Conexión exitosa a SQL Server.")
            for cday in reversed(range(4)):
                check_date = self.date - timedelta(days=cday)
                year = check_date.year
                month = check_date.month
                day = check_date.day

                if not self.employee_id:
                    query_sql = """SELECT usertable.NAME as employee,
                                checking.CHECKTIME as date,
                                DATENAME(WEEKDAY,checking.CHECKTIME) as day,
                                machine.MachineAlias as clock,
                                machine.MachineNumber as CODCLOCK,
                                usertable.SSN as codemployee
                            FROM CHECKINOUT as checking
                            INNER JOIN USERINFO as usertable ON checking.USERID = usertable.USERID
                            INNER JOIN Machines as machine ON checking.SENSORID = machine.MachineNumber
                            WHERE checking.CHECKTIME BETWEEN '%s-%s-%s 00:00:00' AND '%s-%s-%s 23:59:59'
                        """%(year,month,day,year,month,day)
                else:
                    query_sql = """SELECT usertable.NAME as employee,
                                checking.CHECKTIME as date,
                                DATENAME(WEEKDAY,checking.CHECKTIME) as day,
                                machine.MachineAlias as clock,
                                machine.MachineNumber as CODCLOCK,
                                usertable.SSN as codemployee
                            FROM CHECKINOUT as checking
                            INNER JOIN USERINFO as usertable ON checking.USERID = usertable.USERID
                            INNER JOIN Machines as machine ON checking.SENSORID = machine.MachineNumber
                            WHERE checking.CHECKTIME BETWEEN '%s-%s-%s 00:00:00' AND '%s-%s-%s 23:59:59' AND usertable.SSN = '%s'
                        """%(year,month,day,year,month,day, self.employee_id.barcode)
                
                # Ejecutar una consulta de ejemplo
                cursor = conn.cursor()
                cursor.execute(query_sql)
                results = cursor.fetchall()
                code_employees = []
                markings = []
                
                for row in results:
                    code_emp = row[5]
                    date = row[1]
                    clock = row[4]
                    clock_id = self.env['hr.attendance.device'].search([('device_id','=',clock)])
                    if clock_id:
                        vals = {
                            'date': date,
                            'code_clock': clock
                        }
                        if code_emp in code_employees:
                            markings[code_employees.index(code_emp)]['lines'].append(vals)
                        else:
                            code_employees.append(code_emp)
                            markings.append({
                                'code_employee': code_emp,
                                'date': date,
                                'lines': [vals]
                            })

                # Cerrar conexión
                cursor.close()
                if markings:
                    self.create_real_marking(markings, self.option_form)
            conn.close()
        except Exception as e:
            _logger.info(f"Error al conectar a SQL Server: {e}")

    def action_set_timezone(self, machine):
        """Function to set user's timezone to device"""
        machine_ip = machine.ip_address
        zk_port = machine.port
        try:
            # Connecting with the device with the ip and port provided
            zk = ZK(machine_ip, port=zk_port, timeout=15,
                    password=0,
                    force_udp=False, ommit_ping=False)
        except NameError:
            raise UserError(
                _("Pyzk module not Found. Please install it"
                    "with 'pip3 install pyzk'."))
        conn = self.device_connect(zk)
        if conn:
            user_tz = self.env.context.get(
                'tz') or self.env.user.tz or 'UTC'
            user_timezone_time = pytz.utc.localize(fields.Datetime.now())
            user_timezone_time = user_timezone_time.astimezone(pytz.timezone(user_tz))
            conn.set_time(user_timezone_time)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Successfully Set the Time',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise UserError(_(
                "Please Check the Connection"))


    def device_connect(self, zk):
        """Function for connecting the device with Odoo"""
        try:
            conn = zk.connect()
            return conn
        except Exception:
            return False

    def create_real_marking(self, markings, form):
        for mark in markings:
            if form == 'db':
                employee_id = self.env['hr.employee'].search([('barcode','=',mark.get('code_employee'))])
            else:
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
                            clock_id = self.env['hr.attendance.device'].search([('device_id','=',line.get('code_clock'))])
                            if clock_id:
                                self.env['list.marking.employees'].create({
                                    'marking_id': real_marking_id.id,
                                    'clock_id': clock_id.id,
                                    'date': line.get('date') + timedelta(hours=6)
                                })
                    else:
                        actual_marks = len(exist_marking_id.marking_ids)
                        consult_marks = len(mark.get('lines'))
                        if actual_marks < consult_marks:
                            exist_marking_id.write({'state':'draft'})
                            exist_marking_id.write({'lost_marking':True})
                            exist_marking_id.marking_ids.unlink()
                            for line in sorted(mark.get('lines'), key=lambda x: x['date']):
                                clock_id = self.env['hr.attendance.device'].search([('device_id','=',line.get('code_clock'))])
                                if clock_id:
                                    self.env['list.marking.employees'].create({
                                        'marking_id': exist_marking_id.id,
                                        'clock_id': clock_id.id,
                                        'date': line.get('date') + timedelta(hours=6)
                                    })
                        elif actual_marks > consult_marks:
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


