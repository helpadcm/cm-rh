from odoo import http
import base64
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class CustomPortalAbsences(http.Controller):

    @http.route('/absences/record_program_fly', type='http', auth="user", website=True)
    def program_to_fly_portal(self, **kwargs):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        
        if employee_id.program_to_fly == 0:
            program_to_fly = 'No disponible'
        else:
            program_to_fly = employee_id.program_to_fly

        history_absences_ids = request.env['hr.leave'].sudo().search([('employee_id','=',employee_id.id),('holiday_status_id.code','=','PFLY')], order="request_date_from desc")
        routes_ids = request.env['flight.routes'].sudo().search([])

        # Recuperar datos del formulario desde la sesión
        form_data = request.session.pop('form_data', {})
        self.create_default_beneficiary(employee_id)

        values = {
            'beneficiaries_ids': employee_id.beneficiaries_ids,
            'program_to_fly': program_to_fly,
            'history_absences_ids': history_absences_ids,
            'routes': routes_ids,
            'form_data': form_data  # Pasar los datos al template
        }
        return request.render("portal_cm.portal_program_to_fly", values)


    @http.route('/create_beneficiary/submit', type='http', auth="user", methods=["POST"], website=True)
    def create_beneficiary_submit(self, **post):
        user = request.env.user
        company_id = request.env.user.company_id
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        if not employee_id:
            return "Error: No se encontró un empleado vinculado a este usuario. Verifique su configuración en Odoo."

        beneficiary_name = post.get("record_beneficiry_name")
        beneficiary_id = post.get("record_beneficiry_identity")
        beneficiary_relationship = post.get("selection_relationship")
        beneficiary_obs = post.get("record_beneficiry_obs")

        vals = {
            'employee_id': employee_id.id,
            'name': beneficiary_name,
            'identity': beneficiary_id,
            'relationship': beneficiary_relationship,
            'observation': beneficiary_obs
        }
        request.env['beneficiaries.detail.list'].sudo().create(vals)
        self.send_notification('success', "¡¡ Beneficiario creado correctamente  !!")
        return request.redirect('/absences/record_program_fly')


    @http.route('/request_tickets/submit', type='http', auth="user", methods=["POST"], website=True)
    def request_tickets_submit(self, **post):
        user = request.env.user
        company_id = request.env.user.company_id
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        if not employee_id:
            return "Error: No se encontró un empleado vinculado a este usuario. Verifique su configuración en Odoo."

        type_value_id = request.env['hr.leave.type'].sudo().search([('code','=','PFLY')])
        start_date = post.get("initial_date")
        end_date = post.get("final_date")
        exit_route_id = post.get("selection_exit_route")
        return_route_id = post.get("selection_return_route")
        exit_only = post.get("exit_only")
        tickets_request = post.get("record_tickets")
        beneficiary1 = post.get("selection_beneficiary1")
        beneficiary2 = post.get("selection_beneficiary2")
        beneficiary3 = post.get("selection_beneficiary3")
        beneficiary4 = post.get("selection_beneficiary4")
        attachments = request.httprequest.files.getlist('attachments')
        notes = post.get("record_notes")

        date_from = datetime.strptime(start_date, "%Y-%m-%d")
        if not exit_only:
            date_to = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            date_to = date_from
        
        vals = {
            'employee_id': employee_id.id,
            'holiday_status_id': int(type_value_id.id),
            'request_date_from': date_from,
            'holiday_type': 'employee',
            'tickets_request': tickets_request,
            'multi_employee': False,
            'company_id': company_id.id,
            'name': notes
        }
        tickets = []
        if int(tickets_request) == 1:
            tickets.append(int(beneficiary1))
            vals.update({'beneficiary1': int(beneficiary1)})
        elif int(tickets_request) == 2:
            tickets.append(int(beneficiary1))
            tickets.append(int(beneficiary2))
            vals.update({'beneficiary1': int(beneficiary1), 'beneficiary2': int(beneficiary2)})
        elif int(tickets_request) == 3:
            tickets.append(int(beneficiary1))
            tickets.append(int(beneficiary2))
            tickets.append(int(beneficiary3))
            vals.update({'beneficiary1': int(beneficiary1), 'beneficiary2': int(beneficiary2), 'beneficiary3': int(beneficiary3)})
        elif int(tickets_request) == 4:
            tickets.append(int(beneficiary1))
            tickets.append(int(beneficiary2))
            tickets.append(int(beneficiary3))
            tickets.append(int(beneficiary4))
            vals.update({'beneficiary1': int(beneficiary1), 'beneficiary2': int(beneficiary2), 'beneficiary3': int(beneficiary3), 'beneficiary4': int(beneficiary4)})

        validated = False
        if date_to.date() < date_from.date():
            self.send_notification('danger', '¡La fecha de regreso no puede ser menor que la fecha de salida!')
            validated = False
        else:
            validated = True

        if validated:
            if len(set(tickets)) < int(tickets_request):
                self.send_notification('danger', '¡Esta seleccionando beneficiarios repetidos!')
                validated = False
            else:
                validated = True

        if validated:
            if not exit_only:
                if exit_route_id != return_route_id:
                    validated = True
                else:
                    self.send_notification('danger', '¡Las rutas no pueden ser iguales!')
                    validated = False

        if validated:
            if exit_only:
                vals.update({'exit_route_id': exit_route_id, 'exit_only': True, 'request_date_to': date_from})
            else:
                vals.update({'exit_route_id': exit_route_id, 'return_route_id': return_route_id, 'request_date_to': date_to})
            
            leave_id = request.env['hr.leave'].sudo().create(vals)
            for attachment in attachments:
                if attachment.filename:
                    file_content = attachment.read()  # Leer el archivo en bytes
                    encoded_file = base64.b64encode(file_content).decode('utf-8')  # Codificar en base64 y convertir a string
                    request.env['ir.attachment'].sudo().create({
                        'name': attachment.filename,
                        'datas': encoded_file,  # Usar el archivo en base64
                        'res_model': 'hr.leave',
                        'res_id': leave_id.id,
                        'mimetype': attachment.mimetype,
                    })
            self.send_notification('success', '¡Su solicitud a sido registrada correctamente!')
        return request.redirect('/absences/record_program_fly')

    def send_notification(self, type, message):
        request.session['flash_message'] = message
        request.session['flash_message_type'] = f'alert-{type}'
        request.session.modified = True

    def create_default_beneficiary(self, employee):
        create_beneficiary = False
        if employee.beneficiaries_ids:
            exist_default_beneficiary = employee.beneficiaries_ids.filtered(lambda ben: ben.is_employee == True)
            if not exist_default_beneficiary:
                create_beneficiary = True
        else:
            create_beneficiary = True

        if create_beneficiary:
            vals = {
                'employee_id': employee.id,
                'name': employee.name,
                'identity': employee.identification_id,
                'relationship': 'employee',
                'is_employee': True
            }
            request.env['beneficiaries.detail.list'].sudo().create(vals)
