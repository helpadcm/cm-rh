import logging
import re

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, exceptions


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    next_birthday = fields.Date(string="Proximo Cumpleaños", compute='_compute_next_birthday')
    employee_no = fields.Char(
        string="Código de Empleado",
        help="Este código es único para cada empleado y se utiliza para identificarlo en el sistema.",
        compute="get_employee_no"
        )
    branch_id = fields.Many2one(
        'hr.branch',
        string="Sucursal",
        help="Sucursal a la que pertenece el empleado."
        )

    def get_employee_no(self):
        for employee in self:
            employee.employee_no = employee.barcode or employee.pin or ''

    @api.depends('birthday')
    def _compute_next_birthday(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.birthday:
                next_birthday = record.birthday + relativedelta(years=relativedelta(today, record.birthday).years)
                if today > next_birthday:
                    next_birthday += relativedelta(years=1)
                record.next_birthday = next_birthday
            else:
                record.next_birthday = False

    @api.onchange('identification_id')
    def _format_identification_id(self):
        for record in self:
            if record.identification_id:
                formatted_id = record.identification_id.strip().replace('-', '')
                if re.fullmatch("^[0-9]{13}$", formatted_id):
                    record.identification_id = formatted_id
                else:
                    record.identification_id = False
                    raise exceptions.UserError(
                        "El número de identificación debe ser de 13 dígitos numericos.\n"
                        "Tome como referencia el siguiente ejemplo: 0801199912345\n"
                        )
            else:
                record.identification_id = False

    @api.model
    def cron_create_portal_user_to_employee(self):
        employees = self.env['hr.employee'].search([('user_id', '=', False), ('work_email', '!=', False)])

        for employee in employees:
            username = employee.name.replace(' ', '')
            if self.env['res.users'].search([('login', '=', username)]):
                continue

            user = self.env['res.users'].create({
                'name': employee.name,
                'login': username,
                'email': employee.work_email,
                'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
            })
            employee.user_id = user.id
