# -*- coding: utf-8 -*-
{
	'name'		:'Sales CM Airlines',
	'version'	:'1.0',
    'license': 'LGPL-3',
	'author'	:'Oniel, CMAirlines',
    'category': 'Accounting/Accounting',
	'description'	:"""Module for tickets sales quotations airlines.""",
	'depends':['base','sale','cm_cai','account','cm_sales', 'year_budget'],
	'data':[
		'data/paperformat.xml',
		# 'security/ir.model.access.csv',
		'views/sale_order_inh.xml',
		'report/sale_order_cm.xml',
		'report/report_reports.xml'
	],
	'installable':True,
}