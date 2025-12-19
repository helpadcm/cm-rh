# -*- coding: utf-8 -*-
{
	'name'		:'Expenses Request CM Airlines',
	'version'	:'17.0',
    'license': 'LGPL-3',
	'author'	:'Oniel, CMAirlines',
    'category': 'Accounting/Accounting',
	'description'	:"""Module for requesting travel expenses.""",
	'depends':['base','sale','cm_cai','account','mail','hr','hr_expense','cm_cargo_handling','hr_payroll_cm','year_budget','cm_banks'],
	'data':[
		'security/groups.xml',
		'security/ir.model.access.csv',
		# 'data/cron.xml',
		'data/sequences.xml',
		'wizard/assign_expenses_view.xml',
		'wizard/deposit_expenses_view.xml',
		'views/conf_view.xml',
		'views/expenses_request_view.xml',
		'views/expense_inh_view.xml',
        'views/menus.xml',
	],
	'installable':True,
}
