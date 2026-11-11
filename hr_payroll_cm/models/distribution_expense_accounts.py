from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class distributionAccounts(models.Model):
    _name = 'hr.distribution.expense.accounts'
    _description = 'Distribucion cuenta de gastos para asiento de nomina'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string="Descripcion", tracking=True)
    account_id = fields.Many2one('account.account',string="Cuenta contable", tracking=True)
    distribution_line_ids = fields.One2many('line.distribution.expense.accounts','distribution_id',string="Lineas de distribucion", tracking=True)

class lineDistributionAccounts(models.Model):
    _name = 'line.distribution.expense.accounts'
    _description = 'Lineas de distribucion cuenta de gastos para asiento de nomina'
    _order = 'department_id asc'

    distribution_id = fields.Many2one('hr.distribution.expense.accounts',string="Distribucion")
    department_id = fields.Many2one('hr.department',string="Departamento")
    account_budget_id = fields.Many2one('account.budget.account',string="Cuenta presupuestaria")
    process_id = fields.Many2one('crossovered.activity',string="Proceso")