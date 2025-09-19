# -*- coding: utf-8 -*-
{
	'name'		:'Reports CM Airlines',
	'version'	:'17.0',
    'license': 'LGPL-3',
	'author'	:'Oniel, CMAirlines',
    'category': 'Accounting/Accounting',
	'description'	:"""Module for reports in cmairlines.""",
	'depends':['base','sale','cm_cai','cm_sales','settlement','report_xlsx','cm_cargo_handling'],
	'data':[
		'security/ir.model.access.csv',
		'data/paperformat.xml',
		'wizard/invoice_report_view.xml',
		'wizard/view_wizard_account_status.xml',
		'views/company_inh_view.xml',
		'views/menus.xml',
		'reports/report_ticket.xml',
		'reports/report_accounting_seat.xml',
		'reports/report_generalinvoice.xml',
		'reports/view_report_account_status.xml',
		'reports/report_reports.xml'
	],
	'assets': {
		'web.report_assets_common': ['cm_reports/static/src/css/fonts.css']
	},
	'installable':True,
}
