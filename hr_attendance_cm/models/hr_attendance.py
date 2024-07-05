from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    device_id = fields.Many2one(
        'hr.attendance.device',
        string='Device',
        help='Device of the attendance.'
        )

    branch_id = fields.Many2one(
        'hr.branch',
        related='device_id.branch_id',
        string='Branch',
        help='Branch of the attendance device.'
        )
