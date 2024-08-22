import logging
import re

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


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
    certificate = fields.Selection(
        [
            ('university intern', 'University Intern'),
            ('graduate', 'Graduate'),
            ('bachelor', 'Bachelor'),
            ('master', 'Master'),
            ('doctor', 'Doctor'),
            ('engineering', 'Engineering'),
            ('other', 'Other'),
            ], 'Certificate Level', default='other', groups="hr.group_hr_user", tracking=True
        )

    format_identification_id = fields.Char(
        string="Formatted Identification Number",
        help='This is the value of the "ID Number" field formatted with hyphens.',
        compute="_format_identification_with_dashes"
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
    def _format_identification_with_dashes(self):
        for record in self:
            if record.identification_id:
                formatted_identification_with_dashes = (
                    f"{record.identification_id[:4]}-{record.identification_id[4:8]}-"
                    f"{record.identification_id[8:]}")
                record.format_identification_id = formatted_identification_with_dashes
            else:
                record.format_identification_id = False

    @api.model
    def cron_create_portal_user_to_employee(self):
        employees = self.env['hr.employee'].search([('user_id', '=', False), ('work_email', '!=', False)])
        for employee in employees:
            login = employee.work_email
            if self.env['res.users'].search([('login', '=', login)]):
                if not self.env['hr.employee'].search([('user_id.login', '=', login)]):
                    employee.user_id = self.env['res.users'].search([('login', '=', login)], limit=1).id
                    _logger.info("User found for employee %s: %s", employee.name, login)
                continue
            user = self.env['res.users'].create(
                {
                    'name': employee.name,
                    'login': login,
                    'share': True,
                    'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
                    }
                )
            employee.user_id = user.id
            _logger.info("User created for employee %s: %s", employee.name, login)
        _logger.info("Cron job to create portal users executed")

    @api.model
    def cron_award_one_year_badge(self):
        today = fields.Date.today()
        one_year_ago = today - relativedelta(years=1)
        two_years_ago = today - relativedelta(years=2)
        badge = self.env.ref('hr_employee_cm.one_year').id
        if not badge:
            return
        contracts = self.env['hr.contract'].search(
            [
                ('date_end', '=', False),
                ('date_start', '>=', two_years_ago),
                ('date_start', '<=', one_year_ago),
                ]
            )
        if not contracts:
            return
        employees = contracts.mapped('employee_id')
        for employee in employees:
            if employee.user_id:
                badge_user = self.env['gamification.badge.user'].search(
                    [
                        ('badge_id', '=', badge),
                        ('user_id', '=', employee.user_id.id),
                        ], limit=1
                    )
                if not badge_user:
                    self.env['gamification.badge.user'].create(
                        {
                            'user_id': employee.user_id.id,
                            'sender_id': self.env.user.id,
                            'badge_id': badge,
                            'employee_id': employee.id,
                            }
                        )
