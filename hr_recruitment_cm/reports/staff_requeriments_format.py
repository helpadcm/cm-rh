from odoo import models,api
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class staffRequirementReport(models.AbstractModel):
    _name = 'report.hr_recruitment_cm.staff_requeriment_format'
    _description = "Formato de Requerimiento de personal"
 
    @api.model
    def _get_report_values(self, docids, data=None):
        vals = self.get_data(docids)
        return {
            'docs': vals,
        }

    def get_data(self, ids):
        rec_turn_ids = self.env['hr.staff.requirement'].search([('id','in',ids)])
        values = {
            'team_name': team_name,
            'turn': turn,
            'days': days_array,
            'jobs': jobs_list,
            'colors': colors_list
        }
        return values