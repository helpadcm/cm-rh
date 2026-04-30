import base64
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

hours_array = [
        ('0', '12:00 AM'), ('0.5', '12:30 AM'),('1', '1:00 AM'), ('1.5', '1:30 AM'),
        ('2', '2:00 AM'), ('2.5', '2:30 AM'),('3', '3:00 AM'), ('3.5', '3:30 AM'),
        ('4', '4:00 AM'), ('4.5', '4:30 AM'),('5', '5:00 AM'), ('5.5', '5:30 AM'),
        ('6', '6:00 AM'), ('6.5', '6:30 AM'),('7', '7:00 AM'), ('7.5', '7:30 AM'),
        ('8', '8:00 AM'), ('8.5', '8:30 AM'),('9', '9:00 AM'), ('9.5', '9:30 AM'),
        ('10', '10:00 AM'), ('10.5', '10:30 AM'),('11', '11:00 AM'), ('11.5', '11:30 AM'),
        ('12', '12:00 PM'), ('12.5', '12:30 PM'),('13', '1:00 PM'), ('13.5', '1:30 PM'),
        ('14', '2:00 PM'), ('14.5', '2:30 PM'),('15', '3:00 PM'), ('15.5', '3:30 PM'),
        ('16', '4:00 PM'), ('16.5', '4:30 PM'),('17', '5:00 PM'), ('17.5', '5:30 PM'),
        ('18', '6:00 PM'), ('18.5', '6:30 PM'),('19', '7:00 PM'), ('19.5', '7:30 PM'),
        ('20', '8:00 PM'), ('20.5', '8:30 PM'),('21', '9:00 PM'), ('21.5', '9:30 PM'),
        ('22', '10:00 PM'), ('22.5', '10:30 PM'),('23', '11:00 PM'), ('23.5', '11:30 PM')]

class CustomPortalAbsences(http.Controller):

    @http.route('/absences/record_absences_employee', type='http', auth="user", website=True)
    def absences_portal(self, **kwargs):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        domain=['|',('requires_allocation', '=', 'no'),('has_valid_allocation', '=', True),('code','not in',['PFLY','SCP','SCSE']),('company_id','=',employee_id.sudo().company_id.id)]
        types_absences_ids = request.env['hr.leave.type'].sudo().search(domain)
        history_absences_ids = request.env['hr.leave'].sudo().search([('employee_id','=',employee_id.id),('holiday_status_id.code','!=','PFLY'),('number_of_days','>',0)], order="request_date_from desc")
        paid_leave_ids = request.env['paid.leave'].sudo().search([])
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
            'paid_leave_ids': paid_leave_ids,
            'hours': hours_array
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

        record_hours = post.get("record_hours")
        start_hour = post.get("selected_start_hour")
        end_hour = post.get("selected_end_hour")

        paid_leave_id = post.get("selection_paid_leave")

        # Obtener los archivos adjuntos
        uploaded_files = request.httprequest.files.getlist('rec_portal_attachments') # Nombre del campo 'input type="file"'

        type_absence_id = request.env['hr.leave.type'].sudo().search([('id','=',int(type_value))])

        vals = {
            'employee_id': employee_id.id,
            'holiday_status_id': int(type_value),
            'request_date_from': datetime.strptime(start_date, "%Y-%m-%d"),
            'company_id': company_id.id,
            'tickets_request': tickets_request,
            'name': notes
        }

        if type_absence_id.code == 'PGS':
            vals.update({'paid_leave_id': paid_leave_id})

        if not record_hours and not middle_day:
            vals.update({'request_date_to': datetime.strptime(end_date, "%Y-%m-%d")})
        else:
            if record_hours:
                initial_hour = [item for item in hours_array if item[0] == start_hour]
                final_hour = [item for item in hours_array if item[0] == end_hour]
                vals.update({
                    'request_unit_hours': True, 
                    'request_date_to': datetime.strptime(start_date, "%Y-%m-%d"),
                    'request_hour_from': initial_hour[0][0],
                    'request_hour_to': final_hour[0][0],
                })

            if middle_day:
                vals.update({'request_unit_half': True, 'request_date_to': datetime.strptime(start_date, "%Y-%m-%d")})
                if middle_day_opt == 'Mañana':
                    vals.update({'request_date_from_period': 'am'})
                else:
                    vals.update({'request_date_from_period': 'pm'})


        
        leave_id = request.env['hr.leave'].sudo().create(vals)
        leave_created = True
        request_days = leave_id.number_of_days

        # --- Lógica de adjuntos ---
        attachment_ids_to_link = []
        for uploaded_file in uploaded_files:
            if uploaded_file and uploaded_file.filename:
                attachment_data = base64.b64encode(uploaded_file.read())
                # Crea el adjunto
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': uploaded_file.filename,
                    'datas': attachment_data,
                    'res_model': 'hr.leave',    # Modelo al que se adjunta
                    'res_id': leave_id.id,      # ID del registro de la solicitud de ausencia
                    'type': 'binary',
                    'mimetype': uploaded_file.content_type,
                })
                attachment_ids_to_link.append(attachment.id)

        if attachment_ids_to_link:
            leave_id.sudo().write({'supported_attachment_ids': [(6, 0, attachment_ids_to_link)]})

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

        elif type_absence_id.code not in ['VAC','HCOMP']:
            message = """Solicitud creada exitosamente"""
            request.session['flash_message'] = message
            request.session['flash_message_type'] = 'alert-success'

        if not leave_created:
            leave_id.sudo().unlink()

        return request.redirect('/absences/record_absences_employee')

    @http.route('/delete_absence/<int:absences_id>', type="http", auth="user", methods=["POST"], website=True)
    def delete_record(self, absences_id, **kwargs):
        leave_id = request.env['hr.leave'].sudo().search([('id','=',absences_id)])
        if leave_id:
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
        else:
            if code in ['VAC','HCOMP']:
                message = """¡Su solicitud por %s dias ha sido creada exitosamente!"""%(days)
            else:
                message = """¡Su solicitud por %s boleto(s) ha sido creada exitosamente!"""%(days)
            request.session['flash_message'] = message
            request.session['flash_message_type'] = 'alert-success'
            leave_created = True
        return leave_created