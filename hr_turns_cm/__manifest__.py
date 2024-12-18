# -*- coding: utf-8 -*-
{
    'name': 'Turns Registration for CM Airlines',
    'version': '1.0',
    'category': 'Human Resources/Payroll',
    'sequence': 243,
    'summary': 'Turns registration module for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines.
        - Registration turns for teams.
        """,
    'depends': ['hr_payroll'],
    'data': [
        'data/cron.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/teams_view.xml',
        'views/schedules_view.xml',
        'views/turn_registration_view.xml',
        'views/menus.xml',
        ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

    }
