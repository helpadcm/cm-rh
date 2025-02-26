from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class CustomPortalAbsences(http.Controller):

    @http.route('/absences/record_absences_employee', type='http', auth="user", website=True)
    def absences_portal(self, **kwargs):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        employee_company_id = employee_id.company_id.id
        domain=['|',('requires_allocation', '=', 'no'),('has_valid_allocation', '=', True)]
        types_absences_ids = request.env['hr.leave.type'].sudo().search(domain)
        history_absences_ids = request.env['hr.leave'].sudo().search([('employee_id','=',employee_id.id)])
        if employee_id.vacations_day == 0:
            vacations = 'No tiene dias de vacaciones disponibles'
        else:
            vacations = employee_id.vacations_day

        if employee_id.program_to_fly == 0:
            program_to_fly = 'No disponible'
        else:
            program_to_fly = employee_id.program_to_fly

        values = {
            'types_absences_ids': types_absences_ids,
            'history_absences_ids': history_absences_ids,
            'comp_days': employee_id.compensatory_day_string,
            'vacations': vacations,
            'program_to_fly': program_to_fly
        }
        # print ("//////////////////////////")
        # print (values)
        return request.render("portal_cm.portal_employee_absences", values)


    @http.route('/request_absences/submit', type='http', auth="user", methods=["POST"], website=True)
    def request_absences_submit(self, **post):
        user = request.env.user
        company_id = request.env.user.company_id
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        if not employee_id:
            return "Error: No se encontró un empleado vinculado a este usuario. Verifique su configuración en Odoo."

        type_value = post.get("selection_absence_type")
        start_date = post.get("initial_date")
        end_date = post.get("final_date")
        # print ("//////////////////////////")
        # print (datetime.strptime(start_date, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S"))
        # print (a)
        notes = post.get("record_notes")
        vals = {
            'employee_id': employee_id.id,
            'holiday_status_id': int(type_value),
            'request_date_from': datetime.strptime(start_date, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S"),
            'request_date_to': datetime.strptime(end_date, "%Y-%m-%dT%H:%M"),
            'holiday_type': 'employee',
            'multi_employee': False,
            'company_id': company_id.id,
            'name': notes
        }
        request.session['flash_message'] = '¡Ausencia registrada correctamente!'
        request.session['flash_message_type'] = 'alert-success'
        request.session.modified = True
        
        request.env['hr.leave'].sudo().create(vals)

        return request.redirect('/absences/record_absences_employee')