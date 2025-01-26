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

    user_id = fields.Many2one('res.users',string="Usuario",default=_get_user_default)
    team_id = fields.Many2one('hr.work.teams',string="Equipo")
    turn = fields.Selection(string="Turno", selection=lambda self: self.get_options())

    def get_options(self):
        user = self.env.user.id
        turns = self.env['hr.turn.registration'].search(['|',('leader_id.user_id','=',user),('responsible_id.user_id','=',user)])
        options_name = set(turns.mapped('name'))
        return [(opt, opt) for opt in options_name]

    def printFormat(self):
        data = {
                'user_id': self.user_id.id,
                'team_id': self.team_id.id,
                'turn': self.turn
                }
        return self.env.ref('hr_turns_cm.action_planification_format').report_action(self,data=data)