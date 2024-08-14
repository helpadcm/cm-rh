{
    'name': 'Certifications module for CM Airlines',
    'version': '1.0',
    'category': 'Human Resources/Certifications',
    'sequence': 243,
    'summary': 'Certifications modulo for CM Airlines',
    'description': """
        This module provides the necessary functionality for CM Airlines to 
        assign certifications to employees.
        """,
    'depends': ['base', 'hr', 'gamification', 'hr_skills', 'hr_skills_survey'],
    'data': [
        'views/hr_employee_certification_views.xml',
        ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    }
