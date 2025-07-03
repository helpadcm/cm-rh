# -*- coding: utf-8 -*-

from odoo import models, fields, api

class accountPaymentInh(models.Model):
    _inherit = 'account.payment'

    number_odoo10 = fields.Char(string="Numero Odoo 10")

class accountAnalyticInh(models.Model):
    _inherit = 'account.analytic.account'

    number_odoo10 = fields.Char(string="Numero Odoo 10")