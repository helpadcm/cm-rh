# -*- coding: utf-8 -*-
from odoo import api, exceptions, models,fields, _
from datetime import datetime

class costs(models.Model):
    _name = 'aff.costs'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Rubros"

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Codigo")
    cost_type = fields.Selection([('fixed','Fijo'),('variable','Variable'),('leasing','Leasing')],string="Tipo de Rubro")
    description = fields.Char(string="Descripción")

    template_id = fields.Many2one('aff.cost.template', string='Plantilla de Parámetros')