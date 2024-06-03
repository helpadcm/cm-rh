# -*- coding: utf-8 -*-
{
    'name': 'Payroll module for CM Airlines',
    'version': '1.0',
    'category': 'Human Resources/Payroll',
    'sequence': 243 ,
    'summary': 'Planning module for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines.
        - Calculate the bonus based on the extra hours worked according to their contract.
        """,
    'depends': ['hr_payroll', 'hr_contract_cm'],
    'data': [
        'views/hr_payroll_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_payslip_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

}
