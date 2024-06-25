# -*- coding: utf-8 -*-
{
    'name': 'Transportation bonus module for CM Airlines',
    'version': '1.1',
    'category': 'Human Resources/Contract',
    'sequence': 244,
    'summary': 'Transportation bonus module for CM Airlines',
    'description': """
This module has added a series of fields for the management of transportation bonuses 
for CM Airlines employees.
        """,
    'depends': ['hr_contract', 'hr'],
    'data': [
        'views/hr_contract_views.xml',
        'views/hr_employee_views_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

}
