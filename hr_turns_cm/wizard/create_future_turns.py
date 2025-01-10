# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime

class createFutureTurn(models.TransientModel):
    _name = 'hr.future.turns'
    _description = "Crear turnos futuros"

    @api.model
    def _get_user_default(self):
        return self.env.user.id

    start_date = fields.Date(string="Fecha de Inicio")
    end_date = fields.Date(string="Fecha Final")
    user_id = fields.Many2one('res.users',string="Usuario",default=_get_user_default)

    def create_turns(self):
        return True

    