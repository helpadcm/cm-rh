# -*- coding: utf-8 -*-
{
	'name'		:'CM Airlines Newsletter',
	'version'	:'1.0',
    'license': 'LGPL-3',
	'author'	:'Oniel, CMAirlines',
    'category': 'Sales/CRM',
	'description'	:"""Module to capture data from website.""",
	'depends':['base','mail', 'crm'],
	'data':[
		# 'security/groups.xml',
		'security/ir.model.access.csv',
		'views/newsletter_view.xml',
        'views/menus.xml',
	],
	'installable':True,
}
