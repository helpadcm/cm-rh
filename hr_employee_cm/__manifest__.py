# -*- coding: utf-8 -*-
{
    'name': 'Employee module for CM Airlines',
    'version': '1.0',
    'category': 'Human Resources/Employee',
    'sequence': 245,
    'summary': 'Employee module for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines.
        - Gets the employees who have birthdays during the month
        """,
    'depends': ['hr', ],
    'data': [
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

}
