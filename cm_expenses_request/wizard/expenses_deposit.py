from odoo import models, fields, _, api
from datetime import datetime, timedelta, time
from odoo.exceptions import ValidationError


class depositExpenses(models.TransientModel):
    _name = "hr.deposit.expenses"
    _description = "Deposito de reembolso"

    @api.model
    def default_get(self, fields):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        rec = super(depositExpenses, self).default_get(fields)
        req_id = self.env[active_model].search([('id','in',active_ids)])
        account_id = self.env['account.account'].search([('code','=','105.01')])
        if req_id:
            rec.update({
                'date': (datetime.now() - timedelta(hours=6)).date()
            })
            if account_id:
                rec.update({
                    'account_id': account_id.id
                })
        return rec

    journal_id = fields.Many2one('account.journal',string='Diario')
    amount = fields.Float(string="Monto")
    date = fields.Date(string="Fecha")
    account_id = fields.Many2one('account.account',string="Cuenta")

    def create_deposit(self):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        req_id = self.env[active_model].search([('id','in',active_ids)])

        deposit_id = self.env['banks.deposit'].create({
            'journal_id': self.journal_id.id,
            'date': self.date,
            'doc_type': 'deposit',
            'total': self.amount,
            'name': f"""Reembolso {req_id.employee_id.name}""",
            'request_id': req_id.id
        })

        self.env['banks.deposit.name'].create({
            'account_id': self.account_id.id,
            'name': "Reembolso",
            'amount': self.amount,
            'chqmanalitics': req_id.assign_to_id.analytic_account_id.id or False,
            'mcheck_id': deposit_id.id,
            'type': 'cr'
        })
        deposit_id.action_validate()
        req_id.write({'refund_amount': self.amount})