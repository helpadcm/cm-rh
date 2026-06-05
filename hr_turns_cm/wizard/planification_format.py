# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class planificationFormatWizard(models.TransientModel):
    _name = 'hr.planification.format'
    _description = "Imprimir formato de planificacion"

    @api.model
    def _get_user_default(self):
        return self.env.user.id

    @api.model
    def _validate_admin(self):
        is_admin = self.env.user.has_group('hr_turns_cm.manager_turn_cm')
        return is_admin

    user_id = fields.Many2one('res.users',string="Usuario",default=_get_user_default)
    team_id = fields.Many2one('hr.work.teams',string="Equipo")
    turn = fields.Char(string="Turno")
    is_manager = fields.Boolean(string="Es admin", default=_validate_admin)
    start_date = fields.Date(string="Fecha de Inicio")
    end_date = fields.Date(string="Fecha Final")

    @api.onchange('start_date', 'end_date','team_id', 'user_id')
    def get_options(self):
        is_admin = self.env.user.has_group('hr_turns_cm.manager_turn_cm')
        turn_name = 'Sin Planificacion'
        if self.start_date:
            if self.start_date.weekday() != 0:
                turn_name = 'Sin Planificacion'
            else:
                self.end_date = self.start_date + timedelta(days=6)
                if self.user_id and self.team_id:
                    turns = self.env['hr.turn.registration'].search(['|',('leader_id.user_id','=',self.user_id.id),('responsible_id.user_id','=',self.user_id.id),('date','>=',self.start_date),('date','<=',self.end_date)])

                    if set(turns.mapped('name')):
                        turn_name = list(set(turns.mapped('name')))[0]
        self.turn = turn_name

    def printFormat(self):
        if self.turn == 'Sin Planificacion':
            raise ValidationError("No existe planificacion para las fecha seleccionadas")

        if self.start_date.weekday() != 0:
            raise ValidationError("Solo puede seleccionar dias lunes")

        data = {
                'user_id': self.user_id.id,
                'team_id': self.team_id.id,
                'turn': self.turn
                }
        return self.env.ref('hr_turns_cm.action_planification_format').report_action(self,data=data)