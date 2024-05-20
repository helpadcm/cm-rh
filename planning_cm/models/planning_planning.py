from odoo import fields, models


class PlanningRole(models.Model):
    _inherit = 'planning.role'

    department_id = fields.Many2one('hr.department', string='Department')


class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    role_department_id = fields.Many2one(
        'hr.department', string='Role Department', related='role_id.department_id', store=True
        )
