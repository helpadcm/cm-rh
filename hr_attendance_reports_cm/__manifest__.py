{
    'name': 'Attendances report for CM Airlines',
    'version': '1.0',
    'category': 'Human Resources/Attendances',
    'sequence': 241,
    'summary': 'Report of employee attendance',
    'description': """
        This module provides the reports needed for the CM Airlines attendance records.
        """,
    'depends': ['hr', 'hr_attendance', 'hr_contract', 'hr_work_entry_contract'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_attendance_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    }
