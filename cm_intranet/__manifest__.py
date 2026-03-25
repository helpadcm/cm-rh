# -*- coding: utf-8 -*-
{
	'name'		:'Intranet CM Airlines',
	'version'	:'17.0',
    'license': 'LGPL-3',
	'author'	:'Oniel, CMAirlines',
    'category': 'Tools',
	'description'	:"""Module for intranet.""",
	'depends':['base','website','portal','cm_rrhh_management','ps_binary_field_attachment_preview'],
	'data':[
        'security/ir.model.access.csv',
		'views/intranet_category_view.xml',
		'views/intranet_document_view.xml',
		'views/portal_templates.xml',
		'views/menus.xml',
	],
	'installable':True,
}
