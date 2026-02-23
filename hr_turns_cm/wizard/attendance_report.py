# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class attendanceEquipReport(models.TransientModel):
    _name = 'hr.attendance.team'
    _description = "Asitencia de equipo"

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

    def get_attendance(self):
        data = {
            'initial_date': self.start_date,
            'final_date': self.end_date,
            'user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'employee_ids': self.employee_ids
        }
        return self.env.ref('hr_turns_cm.action_attendance_team').report_action(self,data=data)        
