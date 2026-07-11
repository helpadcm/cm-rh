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

    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        if "property_account_receivable_id" in fields_list:
            account_receivable_id = self.env['account.account'].search([('code','=','104.01'),('company_ids','in',[1])])
            if account_receivable_id:
                    res["property_account_receivable_id"] = account_receivable_id.id
        if "property_account_payable_id" in fields_list:
            account_payable_id = self.env['account.account'].search([('code','=','201.01'),('company_ids','in',[1])])
            if account_payable_id:
                res["property_account_payable_id"] = account_payable_id.id

        return res

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

# class paymentInh(models.Model):
#     _inherit = "account.payment"

#     def action_post(self):
#         res = super(paymentInh, self).action_post()
#         for rec in self:
#             print ("############################")
#             print (rec.partner_type)
#             if rec.partner_type in ['supplier','customer']:    
#                 if rec.move_id.name in ['Borrador','/']:
#                     sequence_id = rec.journal_id.sequence_ids.filtered(lambda seq: seq.code2.code == rec.pay_method_type)
#                     if sequence_id:
#                         rec.name = sequence_id.next_by_id()
#                     else:
#                         rec.name = rec.journal_id.sequence_id.next_by_id()
#             rec.move_id.internal_number = rec.move_id.name
#         return res