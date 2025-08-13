# -*- coding: utf-8 -*-
{
	'name'		:'Reports CM Airlines',
	'version'	:'17.0',
    'license': 'LGPL-3',
	'author'	:'Oniel, CMAirlines',
    'category': 'Accounting/Accounting',
	'description'	:"""Module for reports in cmairlines.""",
	'depends':['base','sale','cm_cai','cm_sales','settlement','report_xlsx'],
	'data':[
		'data/paperformat.xml',
		'views/company_inh_view.xml',
		'reports/report_ticket.xml',
		'reports/report_accounting_seat.xml',
		'reports/report_reports.xml'
	],
	'assets': {
		'web.report_assets_common': ['cm_reports/static/src/css/fonts.css']
	},
	'installable':True,
}
