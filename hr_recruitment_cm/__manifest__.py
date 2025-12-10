# -*- coding: utf-8 -*-
{
    'name': 'Recruitment CM Airlines',
    'version': '1.0',
    'category': 'Human Resources/Payroll',
    'sequence': 243,
    'summary': 'Modulo para manejo de reclutamiento CM Airlines',
    'description': """
        Este modulo ayudara al proceso de reclutamiento de personal.
        """,
    'depends': ['hr_payroll','mail','hr_recruitment','hr_contract_cm','base_address_extended'],
    'data': [
        'data/sequence.xml',
        'data/mail_templates.xml',
        'data/paperformat.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'wizard/send_form_view.xml',
        'views/employee_view_inh.xml',
        'views/applicant_inh_view.xml',
        'views/staff_requirement_view.xml',
        'views/recruitment_form_templates.xml',
        'views/menus.xml',
        'reports/recruitment_questionnaire.xml',
        'reports/report_reports.xml'
        ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

    }
