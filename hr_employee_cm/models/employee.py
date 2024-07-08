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
    def crm_create_user(self):
        _logger = logging.getLogger(__name__)
        employees = self.search([])

        Users = self.env['res.users']

        for employee in employees:

            work_email = employee.work_email

            if work_email:
                username, _ = work_email.split('@')

                if not employee.user_id:
                    existing_user = Users.search([('login', '=', work_email)], limit=1)
                    if not existing_user:
                        new_user = Users.create(
                            {
                                'login': work_email,
                                'name': username,
                                'email': work_email,
                                'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
                                }
                            )
                        employee.user_id = new_user.id
                        _logger.info(f'Se creó el usuario: {username}')
                    else:
                        _logger.info(f'El usuario con el correo electrónico {work_email} ya existe.')
                else:
                    _logger.info(f'El empleado {username} ya tiene un usuario asociado.')
            else:
                _logger.info(f'El empleado {employee.name} no tiene un correo electrónico de trabajo.')
