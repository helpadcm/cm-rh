# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, Command
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class processBudgetInh(models.Model):
    _inherit = 'crossovered.activity'

    user_ids = fields.Many2many('res.users', string="Usuarios Permitidos")


class employeeInh(models.Model):
    _inherit = 'hr.employee'

    bank_account_ids = fields.Many2many(
        'res.partner.bank',
        relation='employee_bank_account_rel',
        column1='employee_id',
        column2='bank_account_id',
        domain="[('partner_id', '=', work_contact_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        groups="hr.group_hr_user,cm_expenses_request.group_expenses_request_user,cm_expenses_request.group_expenses_request_boss,cm_expenses_request.group_expenses_request_purchase,cm_expenses_request.group_expenses_request_responsible,cm_expenses_request.group_expenses_request_manager",
        copy=False,
        tracking=True,
        string='Bank Accounts',
        help='Employee bank accounts to pay salaries')