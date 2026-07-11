# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

class turnNotesTeam(models.TransientModel):
    _name = 'turn.notes.team'
    _description = "Registro de notas de turno del empleado"

    @api.model
    def get_notes(self):
        active_id = self.env.context.get('active_id')
        turn_id = self.env['team.hour.record'].browse(active_id)
        if turn_id:
            return turn_id.note
        else:
            return ''

    @api.model
    def get_state(self):
        active_id = self.env.context.get('active_id')
        turn_id = self.env['team.hour.record'].browse(active_id)
        if turn_id:
            return turn_id.state
        else:
            return 'draft'

    note = fields.Text(string="Notas",default=get_notes)
    state = fields.Selection([('draft','Borrador'),('validated','Validado')],string="Estado",default=get_state)

    def add_notes(self):
        active_id = self.env.context.get('active_id')
        turn_id = self.env['team.hour.record'].browse(active_id)
        if turn_id:
            turn_id.write({'note': self.note})
        return True