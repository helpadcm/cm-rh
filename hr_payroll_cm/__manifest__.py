# -*- coding: utf-8 -*-
{
    'name': 'Payroll module for CM Airlines',
    'version': '1.2',
    'category': 'Human Resources/Payroll',
    'sequence': 243,
    'summary': 'Planning module for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines.
        - Calculate the bonus based on the extra hours worked according to their contract.
        """,
    'depends': ['hr_employee_cm', 'hr_payroll', 'hr_contract_cm','hr_work_entry_contract_enterprise','hr_attendance_reports_cm','mail','hr_turns_cm','report_xlsx'],
    'data': [
        'data/paperformat.xml',
        'data/cron.xml',
        'security/ir.model.access.csv',
        'security/groups.xml',
        'views/hr_payroll_views.xml',
        'views/hr_payslip_run_views.xml',
        'views/hr_payslip_views.xml',
        'views/employee_attendance_rec_view.xml',
        'views/rap_view.xml',
        'views/historical_deductions_view.xml',
        'views/hr_contract_views.xml',
        'views/other_incomes_view.xml',
        'reports/hr_payroll_employee_report_view.xml',
        'wizard/load_catorceavo_from_excel_wizard_views.xml',
        'wizard/load_nomina_from_excel_wizard_views.xml',
        'wizard/get_hours_record_view.xml',
        'views/menus.xml',
        'reports/payslip_report.xml',
        'reports/markings_format.xml',
        'reports/report_reports.xml'
        ],
    'assets': {
        'web.assets_backend':['hr_payroll_cm/static/src/css/styles.css']
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

    }
