{
    'name': "CM CAI",
    'summary': """
        Modulo para gestion de uso de cai en el sistemas""",
    'description': """
        Modulo para gestion de uso de cai en el sistemas""",
    'author': 'Oniel Avilez',
    'category': 'Accounting/Accounting',
    'version': "17.0",
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'sale'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cai_management_view.xml',
        'views/sequence_inh.xml',
        'views/account_move_view_inh.xml',
        'views/menus.xml'
    ],
}
