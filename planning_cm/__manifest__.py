# -*- coding: utf-8 -*-
{
    'name': 'Planning module for CM Airlines',
    'version': '1.0',
    'category': 'Human Resources/Planning',
    'sequence': 242,
    'summary': 'Planning modulo for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines.
        """,
    'depends': ['planning', 'hr_work_entry_contract'],
    'data': [
        'security/planning_cm_security.xml',
        'security/ir.model.access.csv',

        'views/planning_views.xml',
        'views/work_entry_views.xml',

        'data/cm_work_entry_type.xml',
        'data/cm_planning_roles.xml',
        ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    }
