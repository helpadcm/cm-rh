from odoo import fields, models, api
from datetime import datetime

class leaveInh(models.Model):
    _inherit = 'hr.leave'

    boss_id = fields.Many2one('res.users',string="Gerente de Area")
    paid_leave_id = fields.Many2one('paid.leave', string="Tipo de permiso")

    @api.model_create_multi
    def create(self, vals):
        res = super(leaveInh, self).create(vals)
        if res.employee_id.parent_id.leave_manager_id:
            res.boss_id = res.employee_id.parent_id.leave_manager_id.id
        return res

    def action_refuse(self):
        if self.holiday_status_id.code == 'VAC' and self.state == 'validate':
            if self.employee_id.vacation_details_ids:
                self.employee_id.vacation_details_ids[0].pending_days += self.number_of_days_display
                
        res = super(leaveInh, self).action_refuse()
        return res