# -*- coding: utf-8 -*-
{
	'name'		:'Banks CM',
	'version'	:'1.1',
	'author'	:'CMAirlines',
	'description': """Banks, 
				This module allows you to manage miscellaneous checks, debits, credits, deposits, 
				checkbooks, banks. 
				Miscellaneous checks:  -You can manage all of miscellaneous checks -If
				you want to make a retention in these checks, you have to use an account that is used for retentions
				Debits and Credist: -You can manage debits and credit, and also create temnplates of and existent document to use it in the future
				Deposits : -You can manage deposits.
				each of these documents have the option to cancel journal entries
				Checkbooks: With this option you can vinculate a journal to a bank and an expecific bank account
				Templates: Use to allow you use documents as templates for the creation of future documents""",

	'depends'	:['base','account','payment','cm_cai','account_accountant'],
	'data'		:[
		'data/paperformat.xml',
		'data/sequence_codes.xml',
		'data/decimal_precision.xml',
		'security/groups.xml',
		'security/ir.model.access.csv',
		# 'data/account_type.xml',
		'wizard/anulation_date_wizard.xml',
		'wizard/template_docid_select.xml',
		'wizard/register_payment_view_inh.xml',
		# 'wizard/anulation_date_voucher_wizard.xml',
		'views/account_payment.xml',
		'views/account_account_view.xml',
		'views/config_journal_view.xml',
		'views/debit_credit_view.xml',
		# 'views/account_invoice_supplier.xml',
		# 'views/account_invoice_customer.xml',
		'views/ir_sequence_view.xml',
		# 'views/layouts.xml',
		'views/mcheck_view.xml',
		'views/deposit.xml',
		# 'views/checkbook_journal_items.xml',
		# 'views/banks_transferences.xml',
		# 'views/banks_checkbooks.xml',
		# 'views/banks_banks_view.xml',
		'views/banks_templates.xml',
		# 'views/account_config_view.xml',
		# 'views/res_partner.xml',
		# 'wizard/consiliation_assig_alias.xml',
		# 'wizard/consiliation_manual_assign.xml',
		# 'views/conciliation_config_lines.xml',
		# 'views/res_currency.xml',
		'views/menus.xml',
		'report/checks_miscelaneo.xml',
		'report/misc_check_providers_report.xml',
		'report/report_reports.xml'
	],
	'license': 'LGPL-3',
	'installable':True,
}

