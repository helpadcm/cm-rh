from odoo import models, fields, _, api
from datetime import datetime, timedelta, time
from odoo.exceptions import ValidationError


class assignExpenses(models.TransientModel):
    _name = "hr.assign.expenses"
    _description = "Asignar viaticos"

    @api.model
    def default_get(self, fields):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        rec = super(assignExpenses, self).default_get(fields)
        req_id = self.env[active_model].search([('id','in',active_ids)])
        account_id = self.env['account.account'].search([('code','=','105.01')])
        journal_id = self.env['account.journal'].search([('code','=','BPLPS')])
        if req_id:
            rec.update({
                'description': f"""Viaticos para {req_id.assign_to_id.name}""",
                'date': (datetime.now() - timedelta(hours=6)).date()
            })
            if account_id:
                rec.update({
                    'account_id': account_id.id
                })
        if journal_id:
            rec.update({'journal_id': journal_id.id})
        return rec

    journal_id = fields.Many2one('account.journal',string='Diario')
    amount = fields.Float(string="Monto")
    description = fields.Char(string="Descripcion")
    date = fields.Date(string="Fecha")
    account_id = fields.Many2one('account.account',string="Cuenta")

    def create_debit(self):
        context = self.env.context
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        req_id = self.env[active_model].search([('id','in',active_ids)])

        pending_expenses_ids = self.env['cm.expenses.request'].search([('assign_to_id','=',req_id.assign_to_id.id)])
        for pen in pending_expenses_ids:
            if pen.state == 'assigned' and not pen.omit_settlement:
                raise ValidationError(f"""No se puede realizar la asignacion de viaticos al empleado {req_id.assign_to_id.name} aun tiene la solicitud {req_id.name} pendiente de liquidar.""")

        debit_id = self.env['debit.credit'].create({
            'journal_id': self.journal_id.id,
            'date': self.date,
            'doc_type': 'debit',
            'total': self.amount,
            'name': self.description,
            'request_id': req_id.id
        })

        self.env['debit.credit.name'].create({
            'account_id': self.account_id.id,
            'name': req_id.purpose,
            'amount': self.amount,
            'chqmanalitics': req_id.assign_to_id.analytic_account_id.id or False,
            'debit_credit_id': debit_id.id,
            'type': 'dr'
        })
        debit_id.action_validate()
        req_id.with_context({'state': 'assigned'}).change_state()