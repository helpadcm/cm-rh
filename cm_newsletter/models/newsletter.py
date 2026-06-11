# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError

class Newsletter(models.Model):    
    _name = 'cm.newsletter.list'
    _description = "Newsletter"

    name = fields.Char(string="Correo")
    language = fields.Char(string="Idioma")
    date = fields.Datetime(string="Fecha y Hora")
    country = fields.Char(string="Pais")