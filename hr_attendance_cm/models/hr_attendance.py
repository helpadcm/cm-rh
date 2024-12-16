from odoo import fields, models
import pymssql
from datetime import datetime, timedelta
import logging

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

    def connect_sql_server(self):
        server = '10.1.4.56'
        database = 'attendance'
        username = 'sa'
        password = "youStrong(@)Password"
        last_date = (datetime.now() - timedelta(days=1)).date()
        _logger = logging.getLogger(__name__)
        _logger.info("####################Intentando conexion######################")
        try:
            # Crear la conexión
            conn = pymssql.connect(
                server=server,
                user=username,
                password=password,
                database=database
            )
            _logger.info("Conexión exitosa a SQL Server.")

            query_sql = """SELECT usertable.NAME as employee,
                        checking.CHECKTIME as date,
                        DATENAME(WEEKDAY,checking.CHECKTIME) as day,
                        machine.MachineAlias as clock,
                        machine.MachineNumber as CODCLOCK,
                        usertable.SSN as codemployee
                    FROM CHECKINOUT as checking
                    INNER JOIN USERINFO as usertable ON checking.USERID = usertable.USERID
                    INNER JOIN Machines as machine ON checking.SENSORID = machine.MachineNumber
                    WHERE checking.CHECKTIME BETWEEN '2024-%s-%s 00:00:00' AND '2024-%s-%s 23:59:59'
                """%(last_date.month,last_date.day,last_date.month,last_date.day)

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
            conn.close()
            self.create_real_marking(markings)
        except Exception as e:
            _logger.info(f"Error al conectar a SQL Server: {e}")

    def create_real_marking(self, markings):
        for mark in markings:
            employee_id = self.env['hr.employee'].search([('barcode','=',mark.get('code_employee'))])
            if employee_id:
                if len(mark.get('lines')) > 0:
                    real_marking_id = self.env['real.marking.employees'].create({
                        'name': '%s %s'%(employee_id.name, mark.get('date').date()),
                        'employee_id': employee_id.id,
                        'date': mark.get('date')
                    })
                    for line in mark.get('lines'):
                        clock_id = self.env['hr.attendance.device'].search([('device_id','=',line.get('code_clock'))])
                        if clock_id:
                            self.env['list.marking.employees'].create({
                                'marking_id': real_marking_id.id,
                                'clock_id': clock_id.id,
                                'date': line.get('date')
                            })