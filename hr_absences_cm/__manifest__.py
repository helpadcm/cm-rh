# -*- coding: utf-8 -*-
{
    'name': 'Absences module for CM Airlines',
    'version': '1.0',
    'category': 'Human Resources/Payroll',
    'sequence': 243,
    'summary': 'Absences module for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines.
        - Administration of the different absences that may occur in the company.
        """,
    'depends': ['hr', 'hr_payroll', 'hr_contract','mail','hr_holidays','hr_contract_cm'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/employee_inh_view.xml',
        'views/flight_routes_view.xml',
        'views/menu.xml',
        ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    }
