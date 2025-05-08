# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.http import request

class HrApplicantInh(models.Model):
    _inherit = 'hr.applicant'

    @api.model
    def default_get(self, fields_list):
        res = super(HrApplicantInh, self).default_get(fields_list)
        job_id = res.get('job_id')
        progress_requirement_id = self.env['hr.staff.requirement'].search([('new_position','=',job_id),('state','=','in_progress')])
        if progress_requirement_id and len(progress_requirement_id) == 1:
            res.update({'requirement_id': progress_requirement_id.id})
        return res

    requirement_id = fields.Many2one('hr.staff.requirement',string="Requerimiento")

    @api.onchange('stage_id')
    def update_hired_persons(self):
        if self.requirement_id and self.stage_id.hired_stage:
            self.requirement_id.hired_qty += 1
            if self.requirement_id.hired_qty == self.requirement_id.requested_qty:
                self.requirement_id.state = 'finalized'