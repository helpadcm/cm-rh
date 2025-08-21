{
    "name": "Retention Payment Integration CM",
    "version": "1.2",
    "depends": ["account","cm_banks","cm_cai","account_accountant","report_xlsx"],
    "author": "CMAirlines",
    "category": "Accounting",
    "description": "Gestiona múltiples retenciones aplicadas a pagos desde el wizard de registro.",
    "data": [
        "data/ret_sequence.xml",
        "data/paperformat.xml",
        "security/groups.xml",
        "security/ir.model.access.csv",
        "wizard/payment_register_inh_view.xml",
        "wizard/view_wizard_retentions.xml",
        "wizard/view_wizard_report_retention.xml",
        "views/company_view_inherit.xml",
        "views/payment_view_inh.xml",
        "views/account_account_view.xml",
        "views/retentions_view.xml",
        "views/menus.xml",
        "report/report_retention.xml",
        "report/retentions_report.xml",
        "report/retention_report.xml",
        "report/report_report.xml"
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3"
}
