# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class exceptionalReason(models.Model):
    _name = 'expense.exceptional.reason'
    _description = "Motivos excepcionales de gastos"

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Codigo")
    skip_exception = fields.Boolean(string="Omitir Excepcion")

    _code_unique = models.Constraint('unique(code)', message='El codigo debe ser unico por motivo de excepcion!')