# -*- coding: utf-8 -*-
{
    'name': 'Planning module for CM Airlines',
    'version': '1.1',
    'category': 'Human Resources/Planning',
    'sequence': 242,
    'author'	:'CMAirlines, Oniel Avilez',
    'summary': 'Planning modulo for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines.
        """,
    'depends': ['base', 'planning'],
    'data': [
        'security/planning_cm_security.xml',
        'security/ir.model.access.csv',

        'views/planning_views.xml',
        'views/work_entry_views.xml',

        'data/cm_work_entry_type.xml',
        'data/cm_planning_roles.xml',

        # 'wizard/cm_work_entry_processing_wizard_view.xml',
        'wizard/load_weekly_planning_wizard_view.xml',
        ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    }
