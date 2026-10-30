# -*- coding: utf-8 -*-
{
    'name': 'Portal CM Airlines',
    'version': '1.3',
    'category': 'Human Resources/Payroll',
    'sequence': 243,
    'author'	:'CMAirlines, Oniel Avilez',
    'summary': 'Portal for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines.
        - Portal actions.
        """,
    'depends': ['portal','hr_turns_cm','hr_holidays', 'hr_absences_cm', 'hr_employee_cm','website','cm_rrhh_management'],
    'data': [
        'data/cron.xml',
        'data/email_templates.xml',
        'data/action_server.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'wizard/turn_notes_view.xml',
        'views/portal_my_home.xml',
        'views/portal_custom_option.xml',
        'views/portal_absences.xml',
        'views/portal_program_fly.xml',
        'views/portal_reserver_room.xml',
        'views/portal_download_signature.xml',
        'views/portal_update_emp_data.xml',
        'views/team_hour_rec_view.xml',
        'views/leave_view_inh.xml',
        'views/menus.xml',
        ],
    'assets': {
        'web.assets_frontend': [
            'portal_cm/static/src/js/portal_absences.js',
            'portal_cm/static/src/css/custom_styles.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

    }
