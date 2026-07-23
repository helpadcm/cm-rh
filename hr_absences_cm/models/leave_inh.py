from odoo import fields, models, api
from datetime import datetime

class leaveInh(models.Model):
    _inherit = 'hr.leave'

    boss_id = fields.Many2one('res.users',string="Gerente de Area")
    paid_leave_id = fields.Many2one('paid.leave', string="Tipo de permiso")
    total_days = fields.Char(string="Total Dias", compute="_get_total_days")

    @api.depends('date_from','date_to')
    def _get_total_days(self):
        for rec in self:
            print ("####################################")
            print (rec.number_of_hours)
            rec.total_days = 'test'

    @api.model_create_multi
    def create(self, vals):
        res = super(leaveInh, self).create(vals)
        if res.employee_id.parent_id.leave_manager_id:
            res.boss_id = res.employee_id.parent_id.leave_manager_id.id
        return res

    def action_refuse(self):
        if self.holiday_status_id.code == 'VAC' and self.state == 'validate':
            if self.employee_id.vacation_details_ids:
                if len(self.employee_id.vacation_details_ids) == 1:
                    self.employee_id.vacation_details_ids[0].pending_days += self.number_of_days
                else:
                    last_line_id = self.employee_id.vacation_details_ids[1]
                    if last_line_id.year == 2:
                        max_days = 12
                    elif last_line_id.year == 3:
                        max_days = 15
                    elif last_line_id.year >= 4:
                        max_days = 20
                    
                    available_days = last_line_id.pending_days
                    diff_days = max_days - available_days
                    self.employee_id.vacation_details_ids[1].pending_days += diff_days
                    self.employee_id.vacation_details_ids[0].pending_days += (self.number_of_days - diff_days)
        res = super(leaveInh, self).action_refuse()
        return res