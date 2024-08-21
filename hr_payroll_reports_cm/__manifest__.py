{
    'name': 'CM Airlines Payroll Reports',
    'version': '1.0',
    'category': 'Human Resources/Payroll',
    'sequence': 242,
    'summary': 'Report of employee payroll',
    'description': """
        This module provides the reports needed for the CM Airlines payroll records.
        """,
    'depends': ['hr', 'hr_contract', 'hr_payroll', 'hr_payroll_cm'],
    'data': [
        'security/ir.model.access.csv',
        'reports/hr_attendance_employee_report_view.xml',
        ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    }
