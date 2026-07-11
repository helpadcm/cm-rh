from odoo import models, fields, _, api
from datetime import datetime, timedelta, time
from odoo.exceptions import ValidationError

months = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

class getAssists(models.TransientModel):
    _name = "hr.get.assists"
    _description = "Obtener Asistencias para puntaje"

    date = fields.Date('Fecha')

    def get_records(self):
        punctuality_obj = self.env['cm.punctuality.ranking']
        employees_ids = self.env['hr.employee'].search([('department_id.apply_ranking','=',True)])
        initial_date = datetime.combine(self.date, time.min)
        final_date = datetime.combine(self.date, time(23,59,59))
        for employee in employees_ids:
            attendance_ids = self.env['hr.attendance'].search([('employee_id','=',employee.id),('check_in','>=',initial_date),('check_in','<=',final_date)])
            if attendance_ids:
                min_check_in = min(attendance_ids.mapped('check_in'))
                attendance_id = attendance_ids.filtered(lambda att: att.check_in == min_check_in)
                first_mark = min_check_in - timedelta(hours=6)
                weekday = first_mark.weekday()
                if employee.template_id:
                    lines_day = employee.template_id.template_line_ids.filtered(lambda line: line.day_opt == str(weekday))
                    if lines_day:
                        initial_hour = int(lines_day.schedule1_in_id.name)
                        hours = initial_hour // 100
                        minutes = initial_hour % 100

                        if minutes == 50:
                            minutes = 30
                            
                        if first_mark.hour < hours:
                            self.create_record(employee, attendance_id)
                        elif first_mark.hour == hours:
                            if first_mark.minute <= minutes:
                                self.create_record(employee, attendance_id)

                elif not employee.template_id and employee.resource_calendar_id:
                    lines_day = employee.resource_calendar_id.attendance_ids.filtered(lambda line: line.dayofweek == str(weekday))
                    if lines_day:
                        initial_hour = min(lines_day.mapped('hour_from'))
                        first_mark_minutes = first_mark.minute
                        if first_mark.hour < initial_hour:
                            self.create_record(employee, attendance_id)
                        elif first_mark.hour == initial_hour and first_mark_minutes == 0:
                            self.create_record(employee, attendance_id)


        record_ids = punctuality_obj.search([], order='points desc')
        for idx, rec in enumerate(record_ids, start=1):
            rec.sequence = idx


    def create_record(self, employee, attendance):
        punctuality_obj = self.env['cm.punctuality.ranking']
        punctuality_id = punctuality_obj.search([('employee_id','=',employee.id)])
        if not punctuality_id:
            vals = {
                'employee_id': employee.id,
                'points': 1,
                'attendance_ids': [(4, attendance.id)]
            }
            punctuality_obj.create(vals)
        else:
            if attendance.id not in punctuality_id.attendance_ids.ids:
                punctuality_id.attendance_ids = [(4, attendance.id)]
                punctuality_id.points += 1