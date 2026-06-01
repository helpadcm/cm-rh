# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta
# import pymssql
import logging
from odoo.exceptions import UserError, ValidationError
import pytz
import requests
# from zk import ZK, const
_logger = logging.getLogger(__name__)
# try:
# except ImportError:
#     _logger.error("Please Install pyzk library.")

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
        clocks_ids = self.env['hr.attendance.device'].search([('device_active','=',True)])
        markings_values = []
        code_employees = []
        for clock in clocks_ids:
            # url = "http://10.1.4.56:8080/markings?ip_str=%s&port_str=%s&date=%s"%(str(clock.ip_address), str(clock.port), self.date)
            url = "http://181.115.21.90:8080/markings?ip_str=%s&port_str=%s&date=%s"%(str(clock.ip_address), str(clock.port), self.date)

            response = requests.get(url)
            if response.status_code == 200:
                markings = response.json()
                if self.employee_id:
                    markings = [mark for mark in markings if mark['user_id'] == self.employee_id.pin]

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
                                'date': self.date,
                                'lines': [vals]
                            })
            else:
                print ("Error de conexion")

        if len(markings_values) > 0:
            self.create_real_marking(markings_values)

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
                                clock_id = self.env['hr.attendance.device'].search([('id','=',new_mark.get('code_clock'))])
                                if clock_id:
                                    self.env['list.marking.employees'].create({
                                        'marking_id': exist_marking_id.id,
                                        'clock_id': clock_id.id,
                                        'date': new_mark_date
                                    })
