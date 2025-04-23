from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class CustomPortalAbsences(http.Controller):

    @http.route('/absences/record_absences_employee', type='http', auth="user", website=True)
    def absences_portal(self, **kwargs):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        employee_company_id = employee_id.company_id.id
        domain=['|',('requires_allocation', '=', 'no'),('has_valid_allocation', '=', True),('code','!=','PFLY')]
        types_absences_ids = request.env['hr.leave.type'].sudo().search(domain)
        history_absences_ids = request.env['hr.leave'].sudo().search([('employee_id','=',employee_id.id),('holiday_status_id.code','!=','PFLY'),('number_of_days','>',0)], order="request_date_from desc")
        if employee_id.vacations_day == 0:
            vacations = 'No tiene dias de vacaciones disponibles'
        else:
            vacations = employee_id.vacations_day

        values = {
            'types_absences_ids': types_absences_ids,
            'vacations_details': employee_id.vacation_details_ids,
            'history_absences_ids': history_absences_ids,
            'comp_days': employee_id.compensatory_day_string,
            'vacations': vacations,
        }
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
        notes = post.get("record_notes")
        tickets_request = post.get("record_tickets")
        middle_day = post.get("record_middle_day")
        middle_day_opt = post.get("selection_period")

        type_absence_id = request.env['hr.leave.type'].sudo().search([('id','=',int(type_value))])


        vals = {
            'employee_id': employee_id.id,
            'holiday_status_id': int(type_value),
            'request_date_from': datetime.strptime(start_date, "%Y-%m-%d"),
            'holiday_type': 'employee',
            'multi_employee': False,
            'company_id': company_id.id,
            'tickets_request': tickets_request,
            'name': notes
        }

        if middle_day:
            vals.update({'request_unit_half': True})
            vals.update({'request_date_to': datetime.strptime(start_date, "%Y-%m-%d")})
            if middle_day_opt == 'Mañana':
                vals.update({'request_date_from_period': 'am'})
            else:
                vals.update({'request_date_from_period': 'pm'})
        else:
            vals.update({'request_date_to': datetime.strptime(end_date, "%Y-%m-%d")})

        
        leave_id = request.env['hr.leave'].sudo().create(vals)
        leave_created = True
        request_days = leave_id.number_of_days
        if type_absence_id.code == 'VAC':
            available_days = employee_id.vacations_day
            leave_created = self.validate_creation(request_days, available_days, request_days, 'VAC')

        if type_absence_id.code == 'HCOMP':
            request_hours = 0
            if request_days >= 1:
                request_hours = request_days * 8
            elif request_days == 0.5:
                request_hours = 4
            available_hours = employee_id.compensatory_hours
            if request_hours > 0:
                leave_created = self.validate_creation(request_hours, available_hours, request_days, 'HCOMP')
            else:
                message = """Ocurrio un problema en la creacion de su solicitud, contacte con el encargado del sistema"""
                request.session['flash_message'] = message
                request.session['flash_message_type'] = 'alert-danger'
                request.session.modified = True        

        if not leave_created:
            leave_id.sudo().unlink()

        return request.redirect('/absences/record_absences_employee')

    def validate_creation(self, req, available, days, code):
        leave_created = False
        if req > available and code != 'VAC':
            if code == 'HCOMP':
                message = """Los dias u horas solicitadas exceden los disponibles.\nDias Solicitados: %s"""%(days)
            else:
                message = """La cantidad solicitada excede su limite asignado o aun no dispone de este beneficio"""

            request.session['flash_message'] = message
            request.session['flash_message_type'] = 'alert-danger'
            request.session.modified = True        
        else:
            if code in ['VAC','HCOMP']:
                message = """¡Su solicitud por %s dias ha sido creada exitosamente!"""%(days)
            else:
                message = """¡Su solicitud por %s boleto(s) ha sido creada exitosamente!"""%(days)
            request.session['flash_message'] = message
            request.session['flash_message_type'] = 'alert-success'
            request.session.modified = True
            leave_created = True
        return leave_created