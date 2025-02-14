# -*- coding: utf-8 -*-
from odoo import api, fields, models
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
    _description = "Validador de turnos"

    date = fields.Date(string="Fecha")
    employee_id = fields.Many2one('hr.employee',string="Empleado")

    def connect_sql_server(self):
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
                user = conn.get_users()
                attendance = conn.get_attendance()
                attendance_filter = [a for a in attendance if a.timestamp.strftime("%Y-%m-%d") == self.date.strftime("%Y-%m-%d")]
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
            self.create_real_marking(markings)

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
                        if actual_marks != consult_marks:
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

