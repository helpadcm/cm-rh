# -*- coding: utf-8 -*-
{
	'name'		:'RRHH Management CM Airlines',
	'version'	:'17.0',
    'license': 'LGPL-3',
	'author'	:'Oniel, CMAirlines',
    'category': 'Human Resources',
	'description'	:"""Module for RRHH management.""",
	'depends':['base','hr', 'mail'],
	'data':[
		# 'data/email_templates.xml',
		'security/groups.xml',
		'security/ir.model.access.csv',
		# 'data/sequence.xml',
		# 'views/external_request.xml',
		# 'views/ticket_request.xml',
		'views/training_view.xml',
        'views/menus.xml',
	],
	'installable':True,
}
