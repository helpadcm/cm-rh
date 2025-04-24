# -*- coding: utf-8 -*-
{
	'name'		:'CM Sales',
	'version'	:'17.0',
	'author'	:'Oniel Avilez',
	'description'	:"""
			the module validate sale, Syncronice Web Service
	""",
	'depends'	:['base','sale','account','stock','account_accountant','analytic','l10n_hn','cm_cai'],
	    'qweb': [

    ],
	'data'		:[
        'data/cron.xml',
		'security/groups.xml',
		'security/ir.model.access.csv',
		# 'data/data_cmsales.xml',
		# 'data/ir_cron_data.xml',
		'views/sale_order.xml',
		'views/sale_statement_view.xml',
		'views/cash_statement_view.xml',
		'views/point_of_sale_view.xml',
		'views/transactions_view.xml',
		'views/agent_view.xml',
		'views/res_company.xml',
		'views/account_move_inh_view.xml',
		'views/menus.xml',
	],
    'license': 'LGPL-3',
	'installable':True,
}