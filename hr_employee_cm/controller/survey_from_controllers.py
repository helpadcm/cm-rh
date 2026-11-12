# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class EmployeeExitSurveyController(http.Controller):

    @http.route(['/employee/exit/interview'], type='http', auth='public', website=True)
    def employee_exit_survey_form(self, employee_id=None, **kw):
        """Muestra el formulario web de entrevista de salida."""
        employee = None
        if employee_id:
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            
        values = {
            'employee': employee,
            'employee_id': employee_id or '',
        }
        return request.render('hr_employee_cm.employee_exit_survey_template', values)

    @http.route(['/employee/exit/submit'], type='http', auth='public', website=True, methods=['POST'])
    def employee_exit_survey_submit(self, **post):
        """Valida si ya existe la encuesta; si está duplicada, bloquea el guardado por completo."""
        employee_id = post.get('employee_id')
        employee_name = post.get('employee_name')
        
        # 1. Buscar si ya existe una entrevista para este colaborador
        domain = []
        if employee_id:
            domain = [('employee_id', '=', int(employee_id))]
        elif employee_name:
            domain = [('employee_name', '=ilike', employee_name.strip())]

        existing_survey = None
        if domain:
            existing_survey = request.env['employee.exit.survey'].sudo().search(domain, limit=1)

        # 2. BLOQUEO: Si ya existe un registro previo, NO hacemos nada (ni create ni write)
        if existing_survey:
            return request.render('hr_employee_cm.exit_survey_thanks_template', {})

        # 3. Si NO existe, preparamos los valores y creamos el registro por primera vez
        vals = {
            'employee_id': int(employee_id) if employee_id else False,
            'employee_name': employee_name,
            'job_title': post.get('job_title'),
            'department_name': post.get('department_name'),
            'manager_name': post.get('manager_name'),
            'first_contract_date': post.get('first_contract_date') or False,
            'departure_date': post.get('departure_date') or False,
            'seniority': post.get('seniority'),
            'departure_type': post.get('departure_type'),
            'other_departure_text': post.get('other_departure_text'),
            'main_reason': post.get('main_reason'),
            'other_reason_text': post.get('other_reason_text'),
            'other_factors': post.get('other_factors'),
            'q1': post.get('q1'), 'q2': post.get('q2'), 'q3': post.get('q3'), 'q4': post.get('q4'),
            'q5': post.get('q5'), 'q6': post.get('q6'), 'q7': post.get('q7'), 'q8': post.get('q8'),
            'q9': post.get('q9'), 'q10': post.get('q10'), 'q11': post.get('q11'), 'q12': post.get('q12'),
            'positive_aspects': post.get('positive_aspects'),
            'improvement_aspects': post.get('improvement_aspects'),
            'manager_relationship': post.get('manager_relationship'),
            'growth_opportunities': post.get('growth_opportunities'),
            'retention_actions': post.get('retention_actions'),
            'what_would_change': post.get('what_would_change'),
            'would_recommend': post.get('would_recommend'),
            'would_recommend_why': post.get('would_recommend_why'),
            'additional_comments': post.get('additional_comments'),
        }

        request.env['employee.exit.survey'].sudo().create(vals)
        
        return request.render('hr_employee_cm.exit_survey_thanks_template', {})