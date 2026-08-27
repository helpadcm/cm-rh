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

        history_absences = []
        history_absences_ids = request.env['hr.leave'].sudo().search([('employee_id','=',employee_id.id),('holiday_status_id.code','in',['PFLY','SCP','SCSE'])], order="request_date_from desc")
        if history_absences_ids:
            for hist in history_absences_ids:
                if hist.exit_only:
                    ticket_type = 'Solo Ida'
                else:
                    ticket_type = "Ida/Vuelta"

                state = hist._fields['state'].convert_to_export(hist.state, hist)

                history_absences.append({
                    'type': 'Programa a Volar',
                    'description': hist.name,
                    'date_from': (hist.date_from - timedelta(hours=6)).strftime('%d/%m/%Y'),
                    'date_to': (hist.date_to - timedelta(hours=6)).strftime('%d/%m/%Y'),
                    'ticket_type': ticket_type,
                    'tickets_request': hist.tickets_request,
                    'state': state
                })

        history_absences_ids = request.env['rrhh.others.requests'].sudo().search([('employee_id','=',employee_id.id),('tickets_request','=',True)], order="initial_date desc")
        if history_absences_ids:
            for hist in history_absences_ids:
                if hist.exit_only:
                    ticket_type = 'Solo Ida'
                else:
                    ticket_type = "Ida/Vuelta"

                state = hist._fields['state'].convert_to_export(hist.state, hist)

                exit_date = ''
                if hist.exit_date:
                    exit_date = (hist.exit_date - timedelta(hours=6)).strftime('%d/%m/%Y')

                history_absences.append({
                    'type': 'Programa a Volar',
                    'description': hist.observations,
                    'date_from': (hist.initial_date - timedelta(hours=6)).strftime('%d/%m/%Y'),
                    'date_to': exit_date,
                    'ticket_type': ticket_type,
                    'tickets_request': hist.people_qty,
                    'state': state
                })

        routes_ids = request.env['flight.routes'].sudo().search([])
        domain=['|',('requires_allocation', '=', 'no'),('has_valid_allocation', '=', True),('code','in',['PFLY','SCP','SCSE']),('company_id','=',employee_id.company_id.id)]
        types_absences_ids = request.env['hr.leave.type'].sudo().search(domain)

        # Recuperar datos del formulario desde la sesión
        form_data = request.session.pop('form_data', {})
        self.create_default_beneficiary(employee_id)

        values = {
            'beneficiaries_ids': employee_id.beneficiaries_ids,
            'program_to_fly': program_to_fly,
            'history_absences_ids': history_absences,
            'types_absences_ids': types_absences_ids,
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
        birthday = post.get("record_beneficiry_birth")
        beneficiary_relationship = post.get("selection_relationship")
        beneficiary_obs = post.get("record_beneficiry_obs")

        vals = {
            'employee_id': employee_id.id,
            'name': beneficiary_name.upper(),
            'identity': beneficiary_id,
            'birthday': birthday,
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

        type_value_id = post.get("selection_absence_type")
        start_date = post.get("initial_date")
        end_date = post.get("final_date")
        exit_route_id = post.get("selection_exit_route")
        return_route_id = post.get("selection_return_route")
        exit_only = post.get("exit_only")
        open_back = post.get("open_back")
        tickets_request = post.get("record_tickets")
        beneficiary1 = post.get("selection_beneficiary1")
        beneficiary2 = post.get("selection_beneficiary2")
        beneficiary3 = post.get("selection_beneficiary3")
        beneficiary4 = post.get("selection_beneficiary4")
        beneficiary5 = post.get("selection_beneficiary5")
        beneficiary6 = post.get("selection_beneficiary6")
        beneficiary7 = post.get("selection_beneficiary7")
        beneficiary8 = post.get("selection_beneficiary8")
        beneficiary9 = post.get("selection_beneficiary9")
        attachments = request.httprequest.files.getlist('attachments')
        notes = post.get("record_notes")
        program_to_fly = employee_id.program_to_fly

        date_from = datetime.strptime(start_date, "%Y-%m-%d")
        if not exit_only and not open_back:
            date_to = datetime.strptime(end_date, "%Y-%m-%d")
        elif exit_only or open_back:
            date_to = date_from
            if open_back:
                flight_route_id = request.env['flight.routes'].sudo().browse(int(exit_route_id))
                if flight_route_id:
                    exit_destination = flight_route_id.destination
                    exit_origin = flight_route_id.origin
                    ret_route_id = request.env['flight.routes'].sudo().search([('origin','=',exit_destination),('destination','=',exit_origin)])
                    return_route_id = ret_route_id.id

        type_id = request.env['hr.leave.type'].sudo().browse(int(type_value_id))
        business_id = request.env['cm.business.list'].sudo().search([('code','=',type_id.code),('company_id','=',company_id.id)])
        
        vals = {
            'employee_id': employee_id.id,
            'people_qty': str(tickets_request),
            'tickets_request': True,
            'business_id': business_id.id,
            'observations': notes,
            'qty_available': program_to_fly,
            'state': 'draft'
        }
        tickets = []
        if int(tickets_request) == 1:
            tickets.append(int(beneficiary1))
        elif int(tickets_request) == 2:
            tickets.append(int(beneficiary1))
            tickets.append(int(beneficiary2))
        elif int(tickets_request) == 3:
            tickets.append(int(beneficiary1))
            tickets.append(int(beneficiary2))
            tickets.append(int(beneficiary3))
        elif int(tickets_request) == 4:
            tickets.append(int(beneficiary1))
            tickets.append(int(beneficiary2))
            tickets.append(int(beneficiary3))
            tickets.append(int(beneficiary4))
        elif int(tickets_request) == 5:
            tickets.append(int(beneficiary1))
            tickets.append(int(beneficiary2))
            tickets.append(int(beneficiary3))
            tickets.append(int(beneficiary4))
            tickets.append(int(beneficiary5))
        elif int(tickets_request) == 6:
            tickets.append(int(beneficiary1))
            tickets.append(int(beneficiary2))
            tickets.append(int(beneficiary3))
            tickets.append(int(beneficiary4))
            tickets.append(int(beneficiary5))
            tickets.append(int(beneficiary6))
        elif int(tickets_request) == 7:
            tickets.append(int(beneficiary1))
            tickets.append(int(beneficiary2))
            tickets.append(int(beneficiary3))
            tickets.append(int(beneficiary4))
            tickets.append(int(beneficiary5))
            tickets.append(int(beneficiary6))
            tickets.append(int(beneficiary7))
        elif int(tickets_request) == 8:
            tickets.append(int(beneficiary1))
            tickets.append(int(beneficiary2))
            tickets.append(int(beneficiary3))
            tickets.append(int(beneficiary4))
            tickets.append(int(beneficiary5))
            tickets.append(int(beneficiary6))
            tickets.append(int(beneficiary7))
            tickets.append(int(beneficiary8))
        elif int(tickets_request) == 9:
            tickets.append(int(beneficiary1))
            tickets.append(int(beneficiary2))
            tickets.append(int(beneficiary3))
            tickets.append(int(beneficiary4))
            tickets.append(int(beneficiary5))
            tickets.append(int(beneficiary6))
            tickets.append(int(beneficiary7))
            tickets.append(int(beneficiary8))
            tickets.append(int(beneficiary9))

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
            if not exit_only and not open_back:
                if exit_route_id != return_route_id:
                    validated = True
                else:
                    self.send_notification('danger', '¡Las rutas no pueden ser iguales!')
                    validated = False

        if validated:
            if exit_only or open_back:
                if exit_only:
                    vals.update({'fly_exit_route_id': exit_route_id, 'exit_only': True, 'initial_date': date_from, 'exit_date': date_from})
                if open_back:
                    vals.update({'fly_exit_route_id': exit_route_id, 'fly_return_route_id': return_route_id, 'open_back': True, 'initial_date': date_from, 'exit_date': date_from})
            else:
                vals.update({'fly_exit_route_id': exit_route_id, 'fly_return_route_id': return_route_id, 'initial_date': date_from, 'exit_date': date_to})
            
            vals.update({'char_date_from': self.convert_date(date_from), 'char_date_to': self.convert_date(date_to)})
            leave_id = request.env['rrhh.others.requests'].sudo().create(vals)
            for i in tickets:
                beneficiary_id = request.env['request.beneficiary'].sudo().create({
                    'request_id': leave_id.id,
                    'beneficiary_id': i,
                    'employee_id': employee_id.id
                })
                beneficiary_id.sudo().data_beneficiary()
                beneficiary_id.sudo()._onchange_birth_date()

            attachment_ids_to_link = []
            for attachment in attachments:
                if attachment.filename:
                    file_content = attachment.read()  # Leer el archivo en bytes
                    encoded_file = base64.b64encode(file_content).decode('utf-8')  # Codificar en base64 y convertir a string
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': attachment.filename,
                        'datas': encoded_file,  # Usar el archivo en base64
                        'res_model': 'rrhh.others.requests',
                        'res_id': leave_id.id,
                        'mimetype': attachment.mimetype,
                    })
                    attachment_ids_to_link.append(attachment.id)

            if attachment_ids_to_link:
                leave_id.sudo().write({'attachment_ids': [(6, 0, attachment_ids_to_link)]})
            
            leave_id.sudo().with_context({'state': 'to_approve'}).change_state()
            self.send_notification('success', '¡Su solicitud a sido registrada correctamente!')
        return request.redirect('/absences/record_program_fly')

    def send_notification(self, type, message):
        request.session['flash_message'] = message
        request.session['flash_message_type'] = f'alert-{type}'

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
                'birthday': employee.birthday,
                'relationship': 'employee',
                'is_employee': True
            }
            request.env['beneficiaries.detail.list'].sudo().create(vals)

    def convert_date(self, date):
        months = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")
        
        day = date.day
        month = months[date.month]
        year = date.year

        return f"{day} de {month} del {year}"