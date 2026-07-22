from odoo import api, models, fields, _, Command
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

states = [
    ('draft', 'Borrador'),
    ('sent', 'Enviado'),
    ('approved', 'Aprobado'),
    ('done', 'Listo'),
    ('canceled', 'Cancelado')
]

class expensesSheetRequest(models.Model):
    _name = 'expenses.sheet.request'
    _description = "Reporte de Solicitud de viaticos"
    _inherit = ['mail.thread.main.attachment', 'mail.activity.mixin']

    @api.model
    def _default_employee_id(self):
        return self.env.user.employee_id


    name = fields.Char(string="Nombre", tracking=True)
    employee_id = fields.Many2one('hr.employee', string="Empleado", default=_default_employee_id)
    journal_id = fields.Many2one('account.journal', string="Diario", tracking=True)
    user_id = fields.Many2one('res.users', string="Gerente", tracking=True)
    expenses_ids = fields.One2many('hr.expense','expense_sheet_req_id',string="Gastos", tracking=True)
    state = fields.Selection(states, string="Estado", default="draft", tracking=True)
    request_id = fields.Many2one('cm.expenses.request',string="Solicitud de viaticos")
    number = fields.Char("Numero")
    company_id = fields.Many2one('res.company',string="Empresa",required=True,readonly=True,default=lambda self: self.env.company)
    move_id = fields.Many2one('account.move',string="Asiento Contable")
    exception_solution = fields.Selection([('according','Conforme'),('exception','Reembolsado'),('rejected','Rechazado')],string="Solucion de Reembolso")

    advance_amount = fields.Float(string="Anticipo al Empleado", related="request_id.advance_amount")
    total_expense_amount = fields.Float(string="Total de gastos", related="request_id.total_expense_amount")
    infavor_employee_amount = fields.Float(string="A reembolsar", related="request_id.infavor_employee_amount")
    refund_amount = fields.Float(string="Devuelto", related="request_id.refund_amount")

    exeption_id = fields.Many2one('expense.exceptional.reason',string='Motivo de Excepcion',related='request_id.exeption_id')
    description = fields.Text(string="Motivo", related='request_id.description')

    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string="Report Company Currency"
    )
    # === Amount fields === #
    total_amount = fields.Monetary(string="Total", currency_field='company_currency_id',
        compute='_compute_amount', tracking=True)

    untaxed_amount = fields.Monetary(
        string="Subtotal",
        currency_field='company_currency_id',
        compute='_compute_amount')

    total_tax_amount = fields.Monetary(
        string="Impuesto",
        currency_field='company_currency_id',
        compute='_compute_amount')

    exempt_amount = fields.Monetary(string="Monto Excento", currency_field='company_currency_id',
        compute='_compute_amount')

    taxable_amount = fields.Monetary(string="Monto Gravable", currency_field='company_currency_id',
        compute='_compute_amount')

    def change_state(self):
        next_state = self.env.context.get('state')
        if next_state == 'draft':
            if self.request_id:
                self.request_id.state = 'assigned'
                self.expenses_ids.write({'state': 'draft'})
        if next_state == 'approved':
            if self.request_id:
                self.expenses_ids.write({'state': 'approved'})
        if next_state == 'done':
            if self.request_id:
                self.create_move()
                self.request_id.state = 'finalized'
                self.expenses_ids.write({'state': 'posted'})
        self.state = next_state

    def create_move(self):
        source_id = self.env['crossovered.source_expenditure'].search([('code','=','FP')])

        lines = []
        total = 0
        for line in self.expenses_ids:
            total += line.total_amount
            move_line_vals = {
                'name': line.name,
                'account_id': line.account_id.id,
                'analytic_distribution': line.analytic_distribution,
                'analytic_account_id': line.budget_account_id.id,
                'activity_id': line.process_id.id,
                'source_id': source_id.id,
                'debit': line.total_amount
            }
            if self.employee_id.department_id.analytic_account_id:
                analytic = self.employee_id.department_id.analytic_account_id.id
                move_line_vals.update({'analytic_distribution': {str(analytic): 100.0}})
            lines.append((0,0,move_line_vals))

        if self.request_id and self.request_id.refund_amount > 0:
            deposit_ids = request.env['banks.deposit'].sudo().search([('request_id','=',self.request_id.id),('state','=','validated')])
            if deposit_ids:
                for dep in deposit_ids:
                    total += dep.total
                    move_line_vals = {
                        'name': dep.name,
                        'account_id': dep.journal_id.default_account_id.id,
                        'debit': dep.total
                    }
                    lines.append((0,0,move_line_vals))

        if self.infavor_employee_amount > 0:
            desc = ''
            if self.exception_solution == 'exception':
                account_id = self.env['account.account'].search([('code','=','105.01')])
                desc = f"""Reembolso aprobado para el empleado {self.employee_id.name}"""
            elif self.exception_solution in ['rejected','according']:
                account_id = self.env['account.account'].search([('code','=','512.06')])
                desc = f"""Reembolso no realizado para el empleado {self.employee_id.name}"""

            total -= self.infavor_employee_amount
            vals = {
                'name': desc,
                'account_id': account_id.id,
                'credit': self.infavor_employee_amount,
                'partner_id': self.employee_id.sudo().work_contact_id.id,
                'amount_currency': -(self.infavor_employee_amount)
            }
            if self.employee_id.analytic_account_id:
                analytic = self.employee_id.analytic_account_id.id
                vals['analytic_distribution'] = {str(analytic): 100.0}
            lines.append((0, 0, vals))

        
        account_id = self.env['account.account'].search([('code','=','105.01')])
        vals = {
            'name': f'{self.employee_id.name}',
            'account_id': account_id.id,
            'credit': total,
            'partner_id': self.employee_id.sudo().work_contact_id.id,
            'amount_currency': -(total)
        }
        if self.employee_id.analytic_account_id:
            analytic = self.employee_id.analytic_account_id.id
            vals['analytic_distribution'] = {str(analytic): 100.0}
        lines.append((0, 0, vals))

        move_vals = {
            'partner_id': self.employee_id.work_contact_id.id,
            'journal_id': self.journal_id.id,
            'ref': self.name,
            'date': datetime.now().date(),
            'move_type': 'entry',
            'line_ids': lines
        }

        move_id = self.env['account.move'].create(move_vals)
        move_id.action_post()
        self.move_id = move_id.id

    def _get_mail_thread_data_attachments(self):
        self.ensure_one()
        res = super()._get_mail_thread_data_attachments()
        expense_attachments = self.env['ir.attachment'].search(
            [('res_id', 'in', self.expenses_ids.ids), ('res_model', '=', 'hr.expense')],
            order='id desc',
        )
        deposit_ids = self.env['banks.deposit'].search([('request_id','=',self.request_id.id),('state','=','validated')])
        deposit_attachments = self.env['ir.attachment']
        if deposit_ids:
            deposit_attachments = self.env['ir.attachment'].search(
                [('res_id', 'in', deposit_ids.ids), ('res_model', '=', 'banks.deposit')],
                order='id desc',
            )
        if len(deposit_attachments) > 0:
            return res | expense_attachments | deposit_attachments
        else:
            return res | expense_attachments

    @api.depends(
        'expenses_ids',
        'expenses_ids.total_amount', 
        'expenses_ids.tax_amount',
        'expenses_ids.untaxed_amount_currency',
        'expenses_ids.exempt_amount',
        'expenses_ids.total_amount_currency',
        'expenses_ids.tax_ids')
    def _compute_amount(self):
        for sheet in self:
            subtotal = 0
            taxes = 0
            exempt = 0
            extra_exempt_amount = 0
            total = 0
            for expense in sheet.expenses_ids:
                taxes += expense.tax_amount
                subtotal += expense.untaxed_amount_currency
                total += expense.total_amount_currency
                exempt += expense.exempt_amount
                if not expense.tax_ids:
                    exempt += expense.total_amount

                if expense.tax_ids and expense.exempt_amount > 0:
                    extra_exempt_amount += expense.exempt_amount

            sheet.untaxed_amount = subtotal
            sheet.taxable_amount = subtotal + extra_exempt_amount - exempt
            sheet.exempt_amount = exempt
            sheet.total_tax_amount = taxes
            sheet.total_amount = total + extra_exempt_amount


    def show_move(self):
        if self.move_id:
            self.ensure_one()
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'views': [[False, "form"]],
                'res_model': 'account.move',
                'target': 'current',
                'res_id': self.move_id.id
            }

    def get_attachment(self):
        for expense in self.expenses_ids:
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'hr.expense'),
                ('res_id', '=', expense.id),
            ])

            for attachment in attachments:
                attachment.copy({
                    'res_model': self._name,
                    'res_id': self.id,
                })
