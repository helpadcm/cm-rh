# -*- coding: utf-8 -*-
import time
from odoo import api, models, _,fields
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang

ARRAY_GROUP=[
('partner','Contacto'),
('analytic','Analitica'),
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
		data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'company_id', 'group_ledger', 'analytic_account_ids', 'consolidate', 'initial_balance','display_account','sortby','target_move','account_ids','partner_ids'])[0]
		used_context = self._build_contexts(data)
		data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
		if self.env.context.get('export_excel'):
			return self.env.ref('core_report_xls.action_general_ledger_xlsx').report_action(self,data = data)
		return self.with_context(discard_logo_check=True)._print_report(data)

	def _build_contexts(self, data):
		result = {}
		result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
		result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
		result['date_from'] = data['form']['date_from'] or False
		result['date_to'] = data['form']['date_to'] or False
		result['strict_range'] = True if result['date_from'] else False
		result['company_id'] = data['form']['company_id'][0] or False
		return result
