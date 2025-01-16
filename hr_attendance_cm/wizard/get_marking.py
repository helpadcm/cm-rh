# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, timedelta
import pymssql
import logging


class getMarkings(models.TransientModel):
    _name = 'hr.get.markings'
    _description = "Validador de turnos"

    date = fields.Date(string="Fecha")
    employee_id = fields.Many2one('hr.employee',string="Empleado")

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
                    self.create_real_marking(markings)
            conn.close()
        except Exception as e:
            _logger.info(f"Error al conectar a SQL Server: {e}")

    def create_real_marking(self, markings):
        for mark in markings:
            employee_id = self.env['hr.employee'].search([('barcode','=',mark.get('code_employee'))])
            if employee_id:
                if len(mark.get('lines')) > 0:
                    real_marking_obj = self.env['real.marking.employees']
                    exist_marking_id = real_marking_obj.search([('employee_id','=',employee_id.id),('date','=',mark.get('date'))])
                    if not exist_marking_id:
                        real_marking_id = real_marking_obj.create({
                            'name': '%s %s'%(employee_id.name, mark.get('date').date()),
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

