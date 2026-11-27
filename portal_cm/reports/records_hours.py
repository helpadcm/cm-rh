# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, models, fields,_
from collections import defaultdict

class recordHours(models.AbstractModel):
    _name = 'report.portal_cm.hours_record_cm'
    _description = "Horas registradas"

    @api.model
    def _get_report_values(self, docids, data=None):
        res = {}
        data = self.get_data(docids)
        docargs = {
            'data':data,
        }
        return docargs


    def get_data(self,ids):
        rec_ids = self.env['team.hour.record'].search([('id','in',ids)], order="date desc")
        
        # department -> employee -> lista de dicts de registros
        grouped = defaultdict(lambda: defaultdict(list))

        for rec in rec_ids:
            employee = rec.employee_id
            team = rec.team_id

            vals = {
                'employee': employee.name,
                'date': self.change_format(rec.date),
                'day': rec.name_day,
                'turn_type_a': rec.turn_type_a.code,
                'entry1': rec.schedule1_in_id.name,
                'out1': rec.schedule1_out_id.name,
                'turn_type_b': rec.turn_type_b.code,
                'entry2': rec.schedule2_in_id.name,
                'out2': rec.schedule2_out_id.name,
                'total_hours': rec.ordinary_hours,
                'oh': rec.oh,
                'aditional': rec.aditional_hours,
                'notes': rec.note,
            }

            grouped[team][employee].append(vals)

        report_data = []
        for team, employees_dict in grouped.items():
            employees_list = []
            for employee, rows in employees_dict.items():
                employees_list.append({
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'records': rows,
                    'total_ordinary_hours': sum(r['total_hours'] or 0.0 for r in rows),
                    'total_oh': sum(r['oh'] or 0.0 for r in rows),
                    'total_aditional': sum(r['aditional'] or 0.0 for r in rows),
                })

            report_data.append({
                'team_id': team.id,
                'team_name': team.name or 'Sin Equipo',
                'employees': employees_list,
            })
        return report_data

    def change_format(self,date):
        if date:
            formato_fecha = "%d/%m/%Y"
            fecha = datetime.strftime(date, formato_fecha)
            return fecha
