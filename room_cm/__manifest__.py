{
    'name': 'Room module for CM',
    'description': 'Inherit from Room module to add new requirements described in the README.md',
    'author': 'Oniel Avilez',
    'license': 'AGPL-3',
    'depends': ['room'],
    'data': [
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        ],
    'application': True,
    'installable': True,
    'auto_install': False,
    }
