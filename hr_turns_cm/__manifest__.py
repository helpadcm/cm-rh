# -*- coding: utf-8 -*-
{
    'name': 'Turns Registration for CM Airlines',
    'version': '1.2',
    'category': 'Human Resources/Payroll',
    'sequence': 243,
    'summary': 'Turns registration module for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines.
        - Registration turns for teams.
        """,
    'depends': ['hr_payroll','mail'],
    'data': [
        'data/cron.xml',
        'data/action_server.xml',
        'data/email_templates.xml',
        'data/paperformat.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'wizard/validate_turns_view.xml',
        'wizard/furure_turns_view.xml',
        'wizard/planitication_format.xml',
        'views/teams_view.xml',
        'views/schedules_view.xml',
        'views/turn_registration_view.xml',
        'views/employee_inh_view.xml',
        'views/turn_templates_view.xml',
        'views/fortnights.xml',
        'views/email_notifications_view.xml',
        'views/menus.xml',
        'reports/planification_format.xml',
        'reports/report_reports.xml',
        ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

    }
