from odoo import fields, models

class HrLeavesType(models.Model):
    _inherit = 'hr.leave.type'

    code = fields.Char(string="Codigo")