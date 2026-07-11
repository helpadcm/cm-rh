# -*- coding: utf-8 -*-
{
	'name'		:'Survery Modify CM Airlines',
	'version'	:'1.0',
    'license': 'LGPL-3',
	'author'	:'Oniel, CMAirlines',
    'category': 'Tools',
	'description'	:"""Module for survey inherit.""",
	'depends':['base','survey'],
	'data':[
        'security/ir.model.access.csv',
		'views/survey_inh_view.xml',
	],
	'installable':True,
}
