# -*- coding: utf-8 -*-
{
	'name'		:'Reports Accounting',
	'version'	:'17.0',
	'author'	:'Oniel Avilez, CM Airlines',
	'description'	:"""
			Core Reports Xls
	""",
	'depends'	:['account', 'report_xlsx','cm_banks','account_fiscal_year_period','accounting_pdf_reports'],
	    'qweb': [
     
    ],
	'data'		:[
			# 'report/report_contact_list.xml',
			# 'wizard/view_wizard_accounting_report.xml',
			# 'wizard/view_wizard_expire_balances.xml',
			# 'wizard/view_wizard_contact_list.xml',
			# 'wizard/view_business_ledger.xml',
			'wizard/account_wizard_general_ledger_view.xml',
			# 'views/report_accounting_seat.xml',
			# 'views/account_financial_report.xml',
			# 'views/report_financial.xml',
			# 'views/report_aged_inherit.xml',
			'report/report_generalledger.xml',
			'report/report_reports.xml',
			
			],
	'license': 'LGPL-3',
	'installable':True,
	'auto_install':True,
}

