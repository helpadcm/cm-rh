from odoo import api, fields, models


class PlanningRole(models.Model):
    _inherit = 'planning.role'

    department_id = fields.Many2one('hr.department', string='Department')
    cm_color = fields.Char('CM Color')
    work_entry_type_id = fields.Many2one(
        'hr.work.entry.type',
        string='Work Entry Type',
        help=' Work Entry Type to be used for the work entries created from this role, '
             'assume if the default is not set then should not generate work entries'
        )

    @api.constrains('cm_color')
    def _check_color(self):
        for record in self:
            if not record.cm_color:
                continue

            if not record.cm_color.startswith('#'):
                raise ValueError('Color must start with #')
            if len(record.cm_color) != 7:
                raise ValueError('Color must have 7 characters')
            if not record.cm_color[1:].isalnum():
                raise ValueError('Color must be hexadecimal')


class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    role_department_id = fields.Many2one(
        'hr.department', string='Role Department', related='role_id.department_id', store=True
        )
