# -*- coding: utf-8 -*-
{
    'name': "Settlement CM",

    'summary': """
        Modulo de liquidaciones""",

    'description': """
	    - multiples soluciones
    """,

    'author': "CMAirlines",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version'	:'1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account','sale','cm_banks'],
    'license': 'LGPL-3',
    # always loaded
    'data': [
        # 'security/groups.xml',
        # 'security/ir.model.access.csv',
        # 'reports/report_format_paper.xml',       
        # 'views/cierre_de_caja.xml',
        # 'views/res_currency_view.xml',
        'views/account_payment_view.xml',
        # 'views/deposit_view.xml',
        'wizard/register_payment_view.xml',
        'views/journal_view.xml',
        # 'data/data.xml',
        # 'reports/cash_register.xml',
        # 'reports/cash_register_report.xml',
    ]
    # only loaded in demonstration mode
   
}
