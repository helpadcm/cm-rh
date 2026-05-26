# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, Command
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class processBudgetInh(models.Model):
    _inherit = 'crossovered.activity'

    user_ids = fields.Many2many('res.users', string="Usuarios Permitidos")