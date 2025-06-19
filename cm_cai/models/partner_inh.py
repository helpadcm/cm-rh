# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class partnerInh(models.Model):
    _inherit = "res.partner"

    odoo10_id = fields.Integer(string="Id Odoo 10")
    identity = fields.Char(string="Identidad")
    is_customer = fields.Boolean(string="Es Cliente")
    is_supplier = fields.Boolean(string="Es proveedor")
    default_client = fields.Boolean(string="Cliente por defecto")

    cai_ids	= fields.One2many('management.cai','supplier_id','Listado de Numeros Cai Asociados')

class usersInh(models.Model):
    _inherit = "res.users"

    odoo10_id = fields.Integer(string="Id Odoo 10")

class accountTaxInh(models.Model):
    _inherit = "account.tax"

    odoo10_id = fields.Integer(string="Id Odoo 10")

class paymentTermInh(models.Model):
    _inherit = "account.payment.term"

    odoo10_id = fields.Integer(string="Id Odoo 10")

class journalInh(models.Model):
    _inherit = "account.journal"

    odoo10_id = fields.Integer(string="Id Odoo 10")