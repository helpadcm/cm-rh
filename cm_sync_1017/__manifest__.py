{
    'name': "CM Sync 1017",
    'summary': """
        Modulo para sincronizacion odoo 17 con odoo 10""",
    'description': """
        Modulo para sincronizacion odoo 17 con odoo 10""",
    'author': 'Oniel Avilez',
    'category': 'Accounting/Accounting',
    'version': "1.0",
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'sale',
        'cm_cai',
        'cm_banks',
        'cm_retention_register'
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'data/cron.xml',
        'wizard/manual_sync_view.xml',
        'views/move_view_inh.xml'
    ],
}
