# -*- coding: utf-8 -*-
import logging
import re

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)

relationship_select = [
    ('mother', 'Madre'),
    ('father', 'Padre'),
    ('siblings', 'Hermano(a)'),
    ('mother', 'Madre'),
    ('mother', 'Madre'),
]

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

    birthday_month = fields.Integer(string="Mes de nacimiento")

    format_identification_id = fields.Char(
        string="Formatted Identification Number",
        help='This is the value of the "ID Number" field formatted with hyphens.',
        compute="_format_identification_with_dashes"
        )

    employee_age = fields.Integer(string="Edad",compute='_compute_next_birthday')
    relationship = fields.Char(string="Parentesco",tracking=True)
    actual_picture = fields.Binary(string="Fotografia Actual", groups="hr.group_hr_user")

    @api.constrains('barcode')
    def _verify_barcode(self):
        for employee in self:
            if employee.barcode:
                if not (re.match(r'^[A-Za-z0-9]+$', employee.barcode) and len(employee.barcode) <= 18):
                    # raise ValidationError(_("The Badge ID must be alphanumeric without any accents and no longer than 18 characters."))
                    return True

    @api.model
    def _get_certificate_selection(self):
        res = super(HrEmployee, self)._get_certificate_selection()
        return [
            ('primary', self.env._('Primaria')),
            ('secondary', self.env._('Secundaria Completa')),
            ('technical', self.env._('Técnico')),
            ('university_intern', self.env._('Pasante Universitario')),
            ('degree', self.env._('Licenciatura')),
            ('master', self.env._('Maestria')),
            ('doctor', self.env._('Doctorado')),

        ]

    @api.onchange('birthday')
    def calculate_month(self):
        if self.birthday:
            self.birthday_month = self.birthday.month

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

                record.employee_age = (
                    today.year
                    - record.birthday.year
                    - (
                        (today.month, today.day)
                        < (record.birthday.month, record.birthday.day)
                    )
                )
            else:
                record.next_birthday = False
                record.employee_age = 0

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
    def cron_award_one_year_badge(self):
        today = fields.Date.today()
        one_year_ago = today - relativedelta(years=1)
        two_years_ago = today - relativedelta(years=2)
        badge = self.env.ref('hr_employee_cm.one_year').id
        if not badge:
            return
        contracts = self.search(
            [
                ('contract_date_end', '=', False),
                ('contract_date_start', '>=', two_years_ago),
                ('contract_date_start', '<=', one_year_ago),
                ]
            )
        if not contracts:
            return
            
        for employee in contracts:
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

    def action_send_survey(self):
        """Abre la ventana emergente para enviar la entrevista de salida."""
        self.ensure_one()
        email_to = self.work_email or self.private_email or ''
        return {
            'name': _('Enviar Formulario'),
            'type': 'ir.actions.act_window',
            'res_model': 'send.survey',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_emails': email_to,
                'default_employee_id': self.id,
            }
        }

class employeePublicInh(models.Model):
    _inherit = 'hr.employee.public'

    rrhh_boss = fields.Boolean(string="Encargado RRHH")
    function_rrhh = fields.Selection([('rrhh_boss','Encargado RRHH'),('rrhh_manager','Responsable RRHH')],string="Puesto en RRHH")