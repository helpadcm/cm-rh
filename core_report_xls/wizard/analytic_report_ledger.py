# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class analyticAccountLedger(models.TransientModel):
    _name = 'account.analytic.report.ledger'
    _description = "Libro Mayor Cuentas Analiticas"

    @api.model
    def default_get(self, fields):
        rec = super(analyticAccountLedger, self).default_get(fields)
        params = self.env.context.get('params')
        active_ids = self.env.context.get('active_ids')
        if params:
            if params.get('model') == 'account.account':
                rec.update({'account_ids': [(6,0,active_ids)]})
        return rec

    initial_date = fields.Date(string="Fecha de Inicio")
    final_date = fields.Date(string="Fecha Final")
    analytic_account_ids = fields.Many2many('account.analytic.account',string="Cuentas Analiticas")
    account_ids = fields.Many2many('account.account',string="Cuenta")
    partner_ids = fields.Many2many('res.partner',string="Contactos")
    group_by = fields.Selection([('analytic','Analitica'),('partner','Contacto'),('account','Cuenta')], default="analytic", string="Agrupar por")

    def print_excel(self):
        datas = {
            'initial_date': self.initial_date,
            'final_date': self.final_date,
            'analytic_account_ids': self.analytic_account_ids.ids,
            'account_ids': self.account_ids.ids,
            'partner_ids': self.partner_ids.ids,
            'group_by': self.group_by
        }
        return self.env.ref('core_report_xls.action_analytic_account_ledger_xlsx').report_action(self, data = datas)