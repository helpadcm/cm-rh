from odoo import models, fields, api, exceptions
from dateutil.relativedelta import relativedelta
import re


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    next_birthday = fields.Date(string="Proximo Cumpleaños", compute='_compute_next_birthday')

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
                        """El número de identificación debe ser de 13 dígitos.""")
            else:
                record.identification_id = False
