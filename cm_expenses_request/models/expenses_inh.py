# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, Command
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class expensesInh(models.Model):
    _inherit = 'hr.expense'

    request_id = fields.Many2one('cm.expenses.request',string="Solicitud de viaticos")
    budget_account_id = fields.Many2one('account.budget.account',string="Cuenta Presupuestaria")
    invoice_number = fields.Char(string="Número de factura")
    reason_expense = fields.Selection([('tour','Gira'),('training','Capacitación')],string="Motivo de gasto")
    process_id = fields.Many2one('crossovered.activity', string="Proceso")
    expense_sheet_req_id = fields.Many2one('expenses.sheet.request', string="Reporte de gasto")

    @api.depends('product_id', 'account_id', 'employee_id')
    def _compute_analytic_distribution(self):
        for expense in self:
            if expense.request_id:
                print ("///////////////////////////////")
                print (expense.request_id)
                if expense.employee_id and expense.employee_id.analytic_account_id:
                    analytic = expense.employee_id.analytic_account_id.id
                    expense.analytic_distribution = {str(analytic): 100.0}
                else:
                    expense.analytic_distribution = False
            else:
                distribution = self.env['account.analytic.distribution.model']._get_distribution({
                    'product_id': expense.product_id.id,
                    'product_categ_id': expense.product_id.categ_id.id,
                    'partner_id': expense.employee_id.work_contact_id.id,
                    'partner_category_id': expense.employee_id.work_contact_id.category_id.ids,
                    'account_prefix': expense.account_id.code,
                    'company_id': expense.company_id.id,
                })
                expense.analytic_distribution = distribution or expense.analytic_distribution

    def action_submit_expenses(self):
        if self.filtered(lambda expense: not expense.is_editable):
            raise UserError(_('No tiene autorización para editar este gasto..'))
        req_id = self.mapped('request_id')
        sheets = self.env['expenses.sheet.request'].create(self._get_default_expense_sheet_values())
        if req_id:
            sheets.write({'request_id': req_id.id})
            sheets.write({'name': f"""Liq. de viaticos {req_id.employee_id.name} solicitud {req_id.name}"""})
            sheets.action_submit_sheet()
        return {
            'name': _('Nuevos reportes de gastos'),
            'type': 'ir.actions.act_window',
            'res_model': 'expenses.sheet.request',
            'context': self.env.context,
            'views': [[False, "list"], [False, "form"]] if len(sheets) > 1 else [[False, "form"]],
            'domain': [('id', 'in', sheets.ids)],
            'res_id': sheets.id if len(sheets) == 1 else False,
        }

    @api.onchange('product_id','reason_expense')
    def _onchange_product_id_set_analytic(self):
        if self.employee_id and self.employee_id.analytic_account_id:
            analytic = self.employee_id.analytic_account_id.id
            self.analytic_distribution = {str(analytic): 100.0}

        if self.product_id:
            if self.reason_expense == 'tour':
                if not self.product_id.budget_account_id:
                    raise ValidationError(f"""No esta configurada una cuenta presupuestaria para giras en la categoria {self.name}""")
                self.budget_account_id = self.product_id.budget_account_id.id
            elif self.reason_expense == 'training':
                if not self.product_id.training_budget_account_id:
                    raise ValidationError(f"""No esta configurada una cuenta presupuestaria para capacitaciones en la categoria {self.name}""")
                self.budget_account_id = self.product_id.training_budget_account_id.id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('request_id'):
                req_id = self.env['cm.expenses.request'].browse(vals.get('request_id'))
                if req_id:
                    employee = req_id.employee_id
                    if employee.analytic_account_id:
                        analytic = employee.analytic_account_id.id
                        vals['analytic_distribution'] = {str(analytic): 100.0}
        res = super().create(vals_list)
        return res

    def _prepare_move_lines_vals(self):
        res = super()._prepare_move_lines_vals()
        if self.budget_account_id:
            res.update({'analytic_account_id': self.budget_account_id.id})
            res.update({'debit': self.price_unit, 'amount_currency': self.price_unit, 'name': f'{self.employee_id.name}: {self.description}'})
        return res

# class expensesSheetInh(models.Model):
#     _inherit = 'hr.expense.sheet'

#     request_id = fields.Many2one('cm.expenses.request',string="Solicitud de viaticos")

#     def action_reset_approval_expense_sheets(self):
#         if self.request_id:
#             self.request_id.write({'state': 'assigned'})
#         res = super(expensesSheetInh, self).action_reset_approval_expense_sheets()
#         return res

#     def _prepare_bills_vals(self):
#         res = super(expensesSheetInh, self)._prepare_bills_vals()
#         line_ids = res.get('line_ids')
#         total = 0
#         for line in line_ids:
#             total += line[2].get('price_unit')
#             expense_id = self.env['hr.expense'].browse(line[2].get('expense_id'))
#             if line[2].get('account_id') == expense_id.account_id.id:
#                 if self.employee_id.department_id.analytic_account_id:
#                     analytic = self.employee_id.department_id.analytic_account_id.id
#                     line[2]['analytic_distribution'] = {str(analytic): 100.0}

#         expense_name = self.name.split('\n')[0][:64]
#         vals = {
#             'name': f'{self.employee_id.name}',
#             'account_id': 1089,
#             'credit': total,
#             'partner_id': False if self.payment_mode == 'company_account' else self.employee_id.sudo().work_contact_id.id,
#             'amount_currency': -(total)
#         }
#         if self.employee_id.analytic_account_id:
#             analytic = self.employee_id.analytic_account_id.id
#             vals['analytic_distribution'] = {str(analytic): 100.0}
#         line_ids.append(Command.create(vals))
#         res.update({'move_type': 'entry'})
#         self.state = 'done'
#         return res

#     @api.depends('account_move_ids.payment_state', 'account_move_ids.amount_residual')
#     def _compute_from_account_move_ids(self):
#         for sheet in self:
#             if sheet.payment_mode == 'company_account':
#                 if sheet.account_move_ids:
#                     # when the sheet is paid by the company, the state/amount of the related account_move_ids are not relevant
#                     # unless all moves have been reversed
#                     sheet.amount_residual = 0.
#                     if sheet.account_move_ids - sheet.account_move_ids.filtered('reversal_move_id'):
#                         sheet.payment_state = 'paid'
#                     else:
#                         sheet.payment_state = 'reversed'
#                 else:
#                     sheet.amount_residual = sum(sheet.account_move_ids.mapped('amount_residual'))
#                     payment_states = set(sheet.account_move_ids.mapped('payment_state'))
#                     if len(payment_states) <= 1:  # If only 1 move or only one state
#                         sheet.payment_state = payment_states.pop() if payment_states else 'not_paid'
#                     elif 'partial' in payment_states or 'paid' in payment_states:  # else if any are (partially) paid
#                         sheet.payment_state = 'partial'
#                     else:
#                         sheet.payment_state = 'not_paid'
#             else:
#                 # Only one move is created when the expenses are paid by the employee
#                 if sheet.account_move_ids:
#                     if sheet.account_move_ids[:1].move_type == 'entry':
#                         sheet.payment_state = 'paid'
#                     else:    
#                         sheet.amount_residual = sum(sheet.account_move_ids.mapped('amount_residual'))
#                         sheet.payment_state = sheet.account_move_ids[:1].payment_state
#                 else:
#                     sheet.amount_residual = 0.0
#                     sheet.payment_state = 'not_paid'

#     def action_sheet_move_create(self):
#         res = super(expensesSheetInh, self).action_sheet_move_create()
#         self.request_id.write({'state': 'finalized'})
#         return res

class productInh(models.Model):
    _inherit = 'product.product'

    budget_account_id = fields.Many2one('account.budget.account',string="Cuenta Presupuestaria Giras")
    training_budget_account_id = fields.Many2one('account.budget.account',string="Cuenta Presupuestaria Capacitaciones")

class debitCreditInh(models.Model):
    _inherit = 'debit.credit'

    request_id = fields.Many2one('cm.expenses.request',string="Solicitud de viaticos")

class depositInh(models.Model):
    _inherit = 'banks.deposit'

    request_id = fields.Many2one('cm.expenses.request',string="Solicitud de viaticos")