# -*- coding: utf-8 -*-
{
	'name'		:'Internal Portal CM Airlines',
	'version'	:'1.0',
    'license': 'LGPL-3',
	'author'	:'Oniel, CMAirlines',
    'category': 'Tools',
	'description'	:"""Module for internal portal.""",
	'depends':['base','website','ps_binary_field_attachment_preview','mail'],
	'data':[
		'security/groups.xml',
        'security/ir.model.access.csv',
		'views/internal_category_view.xml',
		'views/internal_document_view.xml',
		'views/menus.xml',
	],
	'installable':True,
}
