# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class attendanceEquipReport(models.TransientModel):
    _name = 'attendance.team.report'
    _description = "Asistencia de equipo"

    @api.model
    def _get_user_default(self):
        return self.env.user.id

    @api.model
    def _validate_admin(self):
        is_admin = self.env.user.has_group('hr_turns_cm.manager_turn_cm')
        return is_admin

    start_date = fields.Date(string="Fecha de Inicio")
    end_date = fields.Date(string="Fecha Final")
    user_id = fields.Many2one('res.users',string="Usuario",default=_get_user_default)
    team_id = fields.Many2one('hr.work.teams',string="Equipo")
    is_manager = fields.Boolean(string="Es admin", default=_validate_admin)
    employee_ids = fields.Many2many('hr.employee',string="Empleados")

    @api.constrains('start_date','end_date')
    def valid_dates(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("La fecha inicial no puede ser mayor que la fecha final")

            today = (datetime.now() - timedelta(hours=6)).date()

            first_day_actual_month = today.replace(day=1)
            last_day_actual_month = first_day_actual_month - timedelta(days=1)

            if self.start_date > last_day_actual_month:
                raise ValidationError("Solo puede obtener registros de asistencias de meses anteriores")

            if self.end_date > last_day_actual_month:
                raise ValidationError("Solo puede obtener registros de asistencias de meses anteriores")

    def get_attendance(self):
        data = {
            'initial_date': self.start_date,
            'final_date': self.end_date,
            'user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'employee_ids': self.employee_ids
        }
        return self.env.ref('hr_turns_cm.action_attendance_team').report_action(self,data=data)        
