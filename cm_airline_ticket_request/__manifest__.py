# -*- coding: utf-8 -*-
{
	'name'		:'Ticket Request CM Airlines',
	'version'	:'1.0',
    'license': 'LGPL-3',
	'author'	:'Oniel, CMAirlines',
    'category': 'Tools',
	'description'	:"""Module for registering flight ticket requests.""",
	'depends':['base','mail','portal_cm'],
	'data':[
		'data/email_templates.xml',
		'security/groups.xml',
		'security/ir.model.access.csv',
		'data/sequence.xml',
		'views/external_request.xml',
		'views/ticket_request.xml',
		'views/pax_list.xml',
        'views/menus.xml',
	],
	'installable':True,
}
