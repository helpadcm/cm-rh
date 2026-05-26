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
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string="Report Company Currency"
    )
    # === Amount fields === #
    total_amount = fields.Monetary(string="Total", currency_field='company_currency_id',
        compute='_compute_amount', store=True, readonly=True,
        tracking=True,
    )
    untaxed_amount = fields.Monetary(
        string="Subtotal",
        currency_field='company_currency_id',
        compute='_compute_amount', store=True, readonly=True,
    )
    total_tax_amount = fields.Monetary(
        string="Impuestos",
        currency_field='company_currency_id',
        compute='_compute_amount', store=True, readonly=True,
    )

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
        return res | expense_attachments

    @api.depends('expenses_ids.total_amount', 'expenses_ids.tax_amount')
    def _compute_amount(self):
        for sheet in self:
            sheet.total_amount = sum(sheet.expenses_ids.mapped('total_amount'))
            sheet.total_tax_amount = sum(sheet.expenses_ids.mapped('tax_amount'))
            sheet.untaxed_amount = sheet.total_amount - sheet.total_tax_amount

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

