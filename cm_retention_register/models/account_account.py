# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class account_account(models.Model):
	_inherit = 'account.account'

	retention_porcent = fields.Float(string='Porcentaje de retencion')
	use_4_retention = fields.Boolean('Usar para retenciones', help="If you check this option, this account will be used for retentions in Miscellaneous checks")
	tax_description = fields.Char(string='Descripción del impuesto')
	retention_concept = fields.Char(string="Concepto de Retencion")