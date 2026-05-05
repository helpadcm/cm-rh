# -*- coding: utf-8 -*-
import base64
from odoo import http
from odoo.http import request

class RecruitmentPublicForm(http.Controller):

    @http.route('/job/apply/<int:requirement_id>', type='http', auth='public', website=True)
    def recruitment_form(self, requirement_id, **kw):
        jobs = request.env['hr.job'].sudo().search([])
        return request.render('hr_recruitment_cm.recruitment_public_form', {'jobs': jobs, 'requirement_id': requirement_id})

    @http.route('/job/apply/submit', type='http', auth='public', website=True, methods=['POST'], csrf=False)
    def recruitment_form_submit(self, **post):

        requirement_id = request.env['hr.staff.requirement'].sudo().browse(int(post.get('requirement')))
        """Guardar formulario de postulante"""
        interviewer_ids = [(4, requirement_id.sudo().requested_by.id)]
        if requirement_id.sudo().follower_ids:
            for follower in requirement_id.sudo().follower_ids:
                interviewer_ids.append((4, follower.id))

        vals = {
            'requirement_id': requirement_id.id,
            'department_id': requirement_id.sudo().department_id.id or False,
            'interviewer_ids': interviewer_ids,
            'job_id': requirement_id.sudo().new_position.id or False,
            'name': f"""Postulacion { post.get('partner_name') }""",
            'partner_name': post.get('partner_name'),
            'email_from': post.get('email_from'),
            'identity': post.get('identity'),
            'birthday': post.get('birthday'),
            'city': post.get('city'),
            'address': post.get('address'),
            'immediate_availability': post.get('immediate_availability') == 'on',
            'negotiable': post.get('negotiable') == 'on',
            'marital_status': post.get('marital_status'),
            'children': post.get('children'),
            'academic_level': post.get('academic_level'),
            'last_institute': post.get('last_institute'),
            'graduation_year': post.get('graduation_year'),
            'career_name': post.get('career_name'),
            'currently_studying': post.get('currently_studying') == 'on',
            'current_institute': post.get('current_institute'),
            'career_promedy': post.get('career_promedy'),
            'own_vehicle': post.get('own_vehicle'),
            'has_with': post.get('has_with'),
            'availability_travel': post.get('availability_travel') == 'on',
            'excel_level': post.get('excel_level'),
            'english_level': post.get('english_level'),
            'partner_mobile': post.get('partner_mobile'),
            'banpais_relation': post.get('banpais_relation') == 'on',
            'vigent_licence': post.get('vigent_licence') == 'on',
            'unemployed': post.get('unemployed'),
            'expectatives': post.get('expectatives'),
            'experience': post.get('experience'),
            'knowledge_position': post.get('knowledge_position'),
            'personal_experience': post.get('personal_experience'),
            'salary_expected': post.get('salary_expected'),
            'banpais_situation': post.get('banpais_situation'),
            'disease': post.get('disease') == 'on',
            'other_responsabilities': post.get('other_responsabilities'),
            'free_time': post.get('free_time'),
            'with_life': post.get('with_life'),
            'plans': post.get('plans'),
            # 'job_id': int(post.get('job_id')) if post.get('job_id') else False,
        }

        applicant = request.env['hr.applicant'].sudo().create(vals)
        applicant.sudo().calculate_age()

        # Crear hasta 3 historiales laborales
        for i in range(1, 4):
            company = post.get(f'company_name_{i}')
            if company:
                request.env['applicant.laboral.history'].sudo().create({
                    'applicant_id': applicant.id,
                    'company_name': company,
                    'position_name': post.get(f'position_name_{i}'),
                    'time_worked': post.get(f'time_worked_{i}'),
                    'salary': post.get(f'salary_{i}'),
                    'reason': post.get(f'reason_{i}'),
                    'functions': post.get(f'functions_{i}'),
                    'tastes': post.get(f'tastes_{i}'),
                    'no_tastes': post.get(f'no_tastes_{i}'),
                })

        for i in range(1, 4):
            relation_name = post.get(f'relation_name_{i}')
            if relation_name:
                request.env['applicant.relation.collaborator'].sudo().create({
                    'applicant_id': applicant.id,
                    'name': relation_name,
                    'relationship': post.get(f'relationship_name_{i}'),
                    'currently_work': post.get(f'currently_work_{i}'),
                    'branch': post.get(f'branch_{i}'),
                    'department': post.get(f'department_{i}')
                })
                
        for i in range(1, 4):
            laboral_name = post.get(f'laboral_name_{i}')
            if laboral_name:
                request.env['applicant.laboral.reference'].sudo().create({
                    'applicant_id': applicant.id,
                    'name': laboral_name,
                    'company': post.get(f'lcompany_name_{i}'),
                    'position': post.get(f'lposition_{i}'),
                    'phone': post.get(f'lphone_{i}'),
                })

        for i in range(1, 4):
            p_personal_name = post.get(f'p_personal_name_{i}')
            if p_personal_name:
                request.env['applicant.personal.reference'].sudo().create({
                    'applicant_id': applicant.id,
                    'name': p_personal_name,
                    'relationship': post.get(f'p_relationship_{i}'),
                    'phone': post.get(f'p_phone_{i}'),
                    'company': post.get(f'p_company_name_{i}'),
                })

        file = request.httprequest.files.get('cv_file')
        if file:
            attachment = request.env['ir.attachment'].sudo().create({
                'name': file.filename,
                'res_model': 'hr.applicant',   # o su modelo personalizado
                'res_id': applicant.id,
                'type': 'binary',
                'datas': base64.b64encode(file.read()),
                'mimetype': file.content_type,
            })

        return request.render('hr_recruitment_cm.recruitment_thank_you', {'applicant': applicant})
