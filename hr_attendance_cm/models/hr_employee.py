from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    attendance_device_ids = fields.Many2many(
        'hr.attendance.device',
        string='Attendance Devices',
        help='Attendance devices of the employee.'
        )
