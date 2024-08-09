# -*- coding: utf-8 -*-
{
    'name': 'Employee module for CM Airlines',
    'version': '1.0.1',
    'category': 'Human Resources/Employee',
    'sequence': 245,
    'summary': 'Employee module for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines.
        - Gets the employees who have birthdays during the month
        """,
    'depends': ['hr', 'hr_gamification', ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_branch_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_employee_public_views.xml',
        'data/cron_create_portal_user_to_employee.xml',
        'data/cron_award_one_anniversary_badge.xml',
        'data/gamification_badge_data_cm.xml',
        ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

    }
