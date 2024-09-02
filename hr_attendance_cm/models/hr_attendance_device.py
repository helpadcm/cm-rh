from odoo import fields, models


class HrAttendanceDevice(models.Model):
    _name = 'hr.attendance.device'
    _description = 'Attendance Device'

    name = fields.Char(
        string='Name',
        required=True,
        help='Name of the attendance device.'
        )

    device_id = fields.Char(
        string='Device ID',
        required=True,
        help='Device ID of the attendance device.'
        )

    ip_address = fields.Char(
        string='IP Address',
        required=True,
        help='IP Address of the attendance device.'
        )

    port = fields.Integer(
        string='Port',
        required=True,
        help='Port of the attendance device.',
        default='4370'
        )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        help='Company of the attendance device.'
        )

    branch_id = fields.Many2one(
        'hr.branch',
        string='Branch',
        required=True,
        help='Branch of the attendance device.'
        )

    city_id = fields.Many2one(
        'res.city',
        related='branch_id.city_id',
        string='City',
        required=True,
        help='City of the attendance device.'
        )

    employee_ids = fields.Many2many(
        'hr.employee',
        string='Employees',
        help='Employees of the attendance device.'
        )

    latitude = fields.Float(
        string='Latitude',
        help='Latitude of the attendance device.'
        )

    longitude = fields.Float(
        string='Longitude',
        help='Longitude of the attendance device.'
        )
