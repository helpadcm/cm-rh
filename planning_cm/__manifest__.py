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
    'depends': ['planning', 'hr', 'hr_work_entry_contract_planning','hr_work_entry_contract_planning_attendance','planning_contract'],
    'data': [
        'security/planning_cm_security.xml',
        # 'security/ir.model.access.csv',
        ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    }
