# -*- coding: utf-8 -*-
{
    'name': 'Payroll module for CM Airlines',
    'version': '1.0',
    'category': 'Human Resources/Payroll',
    'sequence': 243 ,
    'summary': 'Planning module for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines.
        """,
    'depends': ['hr_payroll', 'hr'],
    'data': [
        'views/hr_payroll_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

}