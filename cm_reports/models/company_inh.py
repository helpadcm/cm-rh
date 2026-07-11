# -*- coding: utf-8 -*-
from odoo import api, exceptions, models, fields, _

class companyInherit(models.Model):
    _inherit = 'res.company'

    company_motto = fields.Char('Lema de la compañia')