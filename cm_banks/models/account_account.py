# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _

class account_account(models.Model):
	_inherit = 'account.account'
	# _order= "code asc"

	use_4_retention=fields.Boolean('Usar para retenciones', help="If you check this option, this account will be used for retentions in Miscellaneous checks")
	tax_description=fields.Char(string='Descripción del impuesto')