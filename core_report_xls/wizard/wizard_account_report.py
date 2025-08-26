# -*- coding: utf-8 -*-
import time
from odoo import api, models, _,fields
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang

ARRAY_GROUP=[
('partner','Partner'),
('analytic','Analytic'),
]

class AccountReportGeneralLedger(models.TransientModel):
	_inherit = "account.report.general.ledger"
	
	group_ledger = fields.Selection(ARRAY_GROUP,string='Agrupar por')
	# partner_ids = fields.Many2many('res.partner',string="Contactos")
	# analytic_ids = fields.Many2many('account.analytic.account',string="Analitica")
	consolidate = fields.Boolean('Consolidado')
	
	def check_report(self):
		self.ensure_one()
		data = {}
		data['ids'] = self.env.context.get('active_ids', [])
		data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'company_id', 'group_ledger', 'analytic_account_ids', 'consolidate', 'initial_balance'])[0]
		used_context = self._build_contexts(data)
		data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
		return self.with_context(discard_logo_check=True)._print_report(data)
		
	def _excel_report(self, data):
		data = self.pre_print_report(data)
		data['form'].update(self.read(['initial_balance', 'sortby','group_ledger','partner_ids','analytic_account_ids','consolidate'])[0])
		if data['form'].get('initial_balance') and not data['form'].get('date_from'):
			raise UserError(_("Debe definir una fecha de inicio"))
		
		records = self.env[data['model']].browse(data.get('ids', []))
		return {'type': 'ir.actions.report.xml',
				'report_name': 'core_report_xls.report_generalledger.xlsx',
				'datas': data,
				'name': 'General Ledger'
				}	

	def excel_report(self):
		self.ensure_one()
		data = {}
		data['ids'] = self.env.context.get('active_ids', [])
		data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
		used_context = self._build_contexts(data)
		data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
		return self._excel_report(data)

