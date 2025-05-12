# -*- coding: utf-8 -*-
{
    'name': 'Stock module for CM Airlines',
    'version': '1.0',
    'category': 'Stock',
    'sequence': 250,
    'summary': 'Stock modulo for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines.
        """,
    'depends': ['base','stock','maintenance'],
    'data': [
        'views/product_view.xml',
        'views/stock_quant_view.xml',
        'views/maint_equip_view_inh.xml',
        ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    }
