{
    'name': 'Attendances for CM Airlines',
    'version': '1.0',
    'category': 'Human Resources/Attendances',
    'sequence': 241,
    'summary': 'Employee attendance',
    'description': """
        This module provides the requirements for CM Airlines attendance records.
        """,
    'depends': ['base_address_extended', 'hr', 'hr_attendance', 'hr_employee_cm'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_attendance_device_views.xml',
        'views/hr_attendance_views.xml',
        ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    }
