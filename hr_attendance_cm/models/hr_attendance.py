from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    in_device_id = fields.Many2one(
        'hr.attendance.device',
        string='Device Check In',
        help='Device of the attendance.'
        )

    in_branch_id = fields.Many2one(
        'hr.branch',
        related='in_device_id.branch_id',
        string='Branch Check In',
        help='Branch of the attendance device.'
        )

    in_mode = fields.Selection(
        selection_add=[('attendance_system', 'Attendance System')], )

    out_device_id = fields.Many2one(
        'hr.attendance.device',
        string='Device Check Out',
        help='Device of the attendance.'
        )

    out_branch_id = fields.Many2one(
        'hr.branch',
        related='out_device_id.branch_id',
        string='Branch Check Out',
        help='Branch of the attendance device.'
        )

    out_mode = fields.Selection(
        selection_add=[('attendance_system', 'Attendance System')], )
