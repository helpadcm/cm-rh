from odoo import models,api
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class planificationReport(models.AbstractModel):
    _name = 'report.hr_turns_cm.planification_format_cm'
 
    @api.model
    def _get_report_values(self, docids, data=None):
        vals = self.get_data(data.get('user_id'),data.get('team_id'),data.get('turn'))
        return {
            'docs': vals,
        }

    def get_data(self, user_id, team_id, turn):
        rec_turn_ids = self.env['hr.turn.registration'].search(['|',('leader_id.user_id','=',user_id),('responsible_id.user_id','=',user_id),('name','=',turn),('team_id','=',team_id)])
        if rec_turn_ids:
            days_array = []
            for d in sorted(set(rec_turn_ids.mapped('date'))):
                days_array.append(d.day)

            jobs_list = []
            job_ids = []
            employee_ids = []
            employee_list = []
            colors = []
            colors_list = []
            names_types = []
            team_name = ''
            for rec in rec_turn_ids:
                if rec.turn_type_a.color:
                    if rec.turn_type_a.color in colors:
                        colors_list[colors.index(rec.turn_type_a.color)]['names'].append(rec.turn_type_a.name)
                    else:
                        colors.append(rec.turn_type_a.color)
                        colors_list.append({
                            'color': rec.turn_type_a.color,
                            'names': [rec.turn_type_a.name]
                        })

                if rec.turn_type_b.color:
                    if rec.turn_type_b.color in colors:
                        colors_list[colors.index(rec.turn_type_b.color)]['names'].append(rec.turn_type_b.name)
                    else:
                        colors.append(rec.turn_type_b.color)
                        colors_list.append({
                            'color': rec.turn_type_b.color,
                            'names': [rec.turn_type_b.name]
                        })

                team_name = rec.team_id.name
                vals = {
                    'entry_color': rec.turn_type_a.color,
                    'exit_color': rec.turn_type_b.color,
                    'day': rec.date.day,
                    'entry1': rec.schedule1_in_id.name,
                    'out1': rec.schedule1_out_id.name,
                    'entry2': rec.schedule2_in_id.name,
                    'out2': rec.schedule2_out_id.name,
                    'oh': rec.ordinary_hours,
                    'ah': rec.aditional_hours
                }
                if rec.employee_id.id in employee_ids:
                    employee_list[employee_ids.index(rec.employee_id.id)]['turns'].append(vals)
                else:
                    employee_list.append({
                        'job_id': rec.employee_id.job_id.id,
                        'job_name': rec.employee_id.job_id.name,
                        'employee': rec.employee_id.name,
                        'turns': [vals]
                    })
                    employee_ids.append(rec.employee_id.id)

            for emp in employee_list:
                emp_vals = {
                    'employee_name': emp.get('employee'), 
                    'turns': emp.get('turns')
                }

                if emp.get('job_id') in job_ids:
                    jobs_list[job_ids.index(emp.get('job_id'))]['employee_array'].append(emp_vals)
                else:
                    jobs_list.append({
                        'job_name': emp.get('job_name'),
                        'employee_array': [emp_vals]
                    })
                    job_ids.append(emp.get('job_id'))

            for cl in colors_list:
                cl.update({'names': set(cl.get('names'))})

            values = {
                'team_name': team_name,
                'turn': turn,
                'days': days_array,
                'jobs': jobs_list,
                'colors': colors_list
            }
            return values
        else:
            raise ValidationError('No hay registros disponibles')