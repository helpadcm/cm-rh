# -*- coding: utf-8 -*-
import calendar
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime, timedelta, time

months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

class punctualutyRankingRRHH(models.Model):    
    _name = 'cm.punctuality.ranking'
    _description = "Ranking de puntualidad"
    _order = "sequence asc"

    employee_id = fields.Many2one('hr.employee',string="Empleado")
    sequence = fields.Integer(string="Posicion")
    points = fields.Integer(string="Puntos")
    attendance_ids = fields.Many2many('hr.attendance',string="Asistencias")

    def action_show_attendance(self):
        self.ensure_one()
        return {
            'name': 'Asistencias',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.attendance',
            'view_mode': 'list',
            'domain': [('id', 'in', self.attendance_ids.ids)]
        }

    def get_records(self):
        employees_ids = self.env['hr.employee'].search([('department_id.apply_ranking','=',True)])
        date = datetime.now() - timedelta(hours=6)
        last_month_day = calendar.monthrange(date.year, date.month)[1]
        initial_date = datetime.combine(date, time.min)
        final_date = datetime.combine(date, time(23,59,59))
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


        record_ids = self.search([], order='points desc')
        for idx, rec in enumerate(record_ids, start=1):
            rec.sequence = idx

        if date.day == last_month_day:
            self.send_email(date)
            self.env['cm.punctuality.ranking'].search([]).unlink()

    def create_record(self, employee, attendance):
        punctuality_id = self.search([('employee_id','=',employee.id)])
        if not punctuality_id:
            vals = {
                'employee_id': employee.id,
                'points': 1,
                'attendance_ids': [(4, attendance.id)]
            }
            self.create(vals)
        else:
            if attendance.id not in punctuality_id.attendance_ids.ids:
                punctuality_id.attendance_ids = [(4, attendance.id)]
                punctuality_id.points += 1

    def send_email(self, date):
        first_place = self.search([('sequence','=',1)])
        email_to = 'kcastellanos@cmairlines.com'

        mail_obj = self.env['mail.mail']
        message = f"""El mes de {months[date.month]} ha finalizado, el empleado con la asistencia y puntualidad mas perfecta ha sido <strong>{first_place.employee_id.name}</strong> con <strong>{first_place.points} puntos.</strong>"""

        body = """
                <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
                        <tr>
                            <td align="center">
                                <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">
                                    <tbody>
                                        <!-- HEADER -->
                                        <tr>
                                            <td align="center" style="min-width: 590px;">
                                                <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                                    <tr>
                                                        <td valign="middle">
                                                            <span style="font-size: 15px;"><strong>Asistencia y Puntualidad</strong></span><br/>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td colspan="2" style="text-align:center;">
                                                            <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <!-- CONTENT -->
                                        <tr>
                                            <td align="center" style="min-width: 590px;">
                                                <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                                    <tr>
                                                        <td valign="top" style="font-size: 13px;">
                                                            <div>
                                                                {message_str}
                                                                <br/>Saludos<br/>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="text-align:center;">
                                                            <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </td>
                        </tr>
                    </table>
            """.format(message_str=message)
        mail_values = {
            'subject': f'Asistencia y Puntualidad',
            'body_html': body,
            'email_to': email_to,
        }
        mail = mail_obj.create(mail_values)
        mail.send()