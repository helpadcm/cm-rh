# -*- coding: utf-8 -*-
{
    'name': 'Portal CM Airlines',
    'version': '1.0',
    'category': 'Human Resources/Payroll',
    'sequence': 243,
    'summary': 'Portal for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines.
        - Portal actions.
        """,
    'depends': ['portal','hr_turns_cm'],
    'data': [
        'data/action_server.xml',
        'security/ir.model.access.csv',
        'wizard/turn_notes_view.xml',
        'views/portal_my_home.xml',
        'views/portal_custom_option.xml',
        'views/team_hour_rec_view.xml',
        'views/menus.xml',
        ],
    'assets': {
        'web.assets_frontend': [
            'portal_cm/static/src/js/portal_calculates.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

    }
