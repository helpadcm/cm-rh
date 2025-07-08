# -*- coding: utf-8 -*-
from odoo import api, exceptions, models, fields, _

class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    conditions = fields.Text('Condiciones de envio')
    acuerdo = fields.Text('Acuerdo de recibido')
    phone_attention = fields.Char('Atencion telefonica')
    whatsapp        =   fields.Char(string="Whatsapp")
    entrust_website =   fields.Char(string="Sitio web encomiendas")
    tgu_int_phone   =   fields.Char(string="Telefono TGU")
    sps_int_phone   =   fields.Char(string="Telefono SPS")

class ResUsersInherit(models.Model):
	_inherit = 'res.users'

	station_id  = fields.Many2one('cargo.station',string="Estacion")

class partnerInherit(models.Model):
    _inherit = 'res.partner'
    _rec_names_search = ['complete_name', 'email', 'ref', 'vat', 'company_registry', 'client_account', 'phone']

    cargo_client = fields.Boolean(string="Cliente de encomiendas")
    fare_classes_ids = fields.Many2many('fare.clases',string="Clases Tarifarias")
    client_account = fields.Char(string="Cuenta de Cliente")

    def write(self,vals):
        if vals.get('cargo_client'):
            if not self.client_account:
                sequence_id = self.env.ref('cm_cargo_handling.sequence_client_account')
                if sequence_id:
                    vals.update({'client_account': sequence_id.next_by_id()})
        res = super(partnerInherit, self).write(vals)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(partnerInherit, self).create(vals_list)
        if res.cargo_client and not res.client_account:
            sequence_id = self.env.ref('cm_cargo_handling.sequence_client_account')
            if sequence_id:
                res.client_account = sequence_id.next_by_id()
        return res