# -*- coding: utf-8 -*-
{
	'name'		:'RRHH Management CM Airlines',
	'version'	:'17.0',
    'license': 'LGPL-3',
	'author'	:'Oniel, CMAirlines',
    'category': 'Human Resources',
	'description'	:"""Module for RRHH management.""",
	'depends':['base','hr', 'mail', 'hr_payroll_cm', 'hr_attendance', 'hr_turns_cm', 'cm_banks', 'portal'],
	'data':[
		'data/cron.xml',
		'data/sequences.xml',
		'data/paperformat.xml',
		'security/groups.xml',
		'security/ir.model.access.csv',
		'wizard/calculate_assists_view.xml',
		'views/inh_models_view.xml',
		'views/training_view.xml',
		'views/punctuality_ranking_view.xml',
		'views/portal_view.xml',
		'views/request_home_view.xml',
		'views/request_loan_view.xml',
		'views/portal_loan_request.xml',
        'views/menus.xml',
		'reports/receipt_deduction.xml',
		'reports/report_reports.xml'
	],
	'installable':True,
}
