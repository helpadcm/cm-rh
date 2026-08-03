import base64
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class updateEmployeeData(http.Controller):

    @http.route('/employee/update_data', type='http', auth="user", website=True)
    def updateData(self, **kwargs):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        country_ids = request.env['res.country'].sudo().search([])

        if employee_id.country_id:
            state_ids = request.env['res.country.state'].sudo().search([('country_id','=',employee_id.country_id.id)])
        else:
            state_ids = request.env['res.country.state'].sudo().search([])

        if employee_id.private_country_id:
            private_state_ids = request.env['res.country.state'].sudo().search([('country_id','=',employee_id.private_country_id.id)])
        else:
            private_state_ids = request.env['res.country.state'].sudo().search([])

        id_create = 'no'
        if employee_id.id_card:
            id_create = 'yes'

        values = {
            'private_email': employee_id.private_email,
            'private_phone': employee_id.private_phone,
            'complete_name': employee_id.legal_name,
            'id_create': id_create,

            'birthday': employee_id.birthday,
            'place_of_birth': employee_id.place_of_birth,
            'sex': employee_id._fields['sex'].convert_to_export(employee_id.sex, employee_id),
            'age': employee_id.employee_age,

            'emergency_contact': employee_id.emergency_contact,
            'relationship': employee_id.relationship,
            'emergency_phone': employee_id.emergency_phone,

            'country_ids': country_ids,
            'country_id': employee_id.country_id.id,
            'identification': employee_id.format_identification_id,
            'ssnid': employee_id.ssnid,
            'passport_id': employee_id.passport_id,
            'is_non_resident': employee_id.is_non_resident,
            'resident_number': employee_id.resident_number,

            'state_ids': state_ids,
            'private_state_ids': private_state_ids,
            'state_id': employee_id.private_state_id.id,
            'city': employee_id.private_city,
            'private_country_id': employee_id.private_country_id.id,
            'address': employee_id.private_street,
            'reference_point': employee_id.private_street2,

            'status': employee_id.marital,
            'children': employee_id.children,

            'certificate': employee_id.certificate,
            'study_field': employee_id.study_field,
            'aeronatical_license': employee_id.aeronatical_license,
            'license_number': employee_id.license_number,
            'license_type': employee_id.license_type,
            'expiration_date_license': employee_id.expiration_date_license
        }
        return request.render("portal_cm.portal_employee_update", values)


    @http.route('/request_update/submit', type='http', auth="user", methods=["POST"], website=True)
    def request_absences_submit(self, **post):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        if not employee_id:
            return "Error: No se encontró un empleado vinculado a este usuario. Verifique su configuración en Odoo."

        private_email = post.get("record_private_email")
        private_phone = post.get("record_private_phone")
        birthday = post.get("record_birthday")
        place_of_birth = post.get("record_place_of_birth")
        emergency_contact = post.get("record_emergency_contact")
        relationship = post.get("record_relationship")
        emergency_phone = post.get("record_emergency_phone")

        country_id = post.get("selection_countries")
        ssnid = post.get("record_ssnid")
        passport_id = post.get("record_passport_id")
        is_non_resident = post.get("is_resident")
        resident_number = post.get("record_resident_number")

        private_state_id = int(post.get("selection_states"))
        private_city = post.get("record_city")
        private_street = post.get("record_address")
        private_street2 = post.get("record_reference_point")
        children = post.get("record_children")

        certificate = post.get("selection_certificate")
        study_field = post.get("record_study_field")
        aeronatical_license = post.get("aeronautical_license")
        license_number = post.get("record_license_number")
        expiration_date_license = post.get("record_expiration_date_license")

        if post.get("selection_certificate") == 'Primaria':
            certificate = 'primary'
        elif post.get("selection_certificate") == 'Secundaria Completa':
            certificate = 'secondary'
        elif post.get("selection_certificate") == 'Técnico':
            certificate = 'technical'
        elif post.get("selection_certificate") == 'Pasante Universitario':
            certificate = 'university_intern'
        elif post.get("selection_certificate") == 'Licenciatura':
            certificate = 'degree'
        elif post.get("selection_certificate") == 'Maestría':
            certificate = 'master'
        elif post.get("selection_certificate") == 'Doctorado':
            certificate = 'doctor'
        else:
            certificate = None  # Valor predeterminado si no coincide con ninguna opción

        if post.get("selection_license_type") == 'Piloto':
            license_type = 'pilot'
        elif post.get("selection_license_type") == 'Tripulante de Cabina':
            license_type = 'cabin_crew'
        elif post.get("selection_license_type") == 'Despachador de Vuelos':
            license_type = 'flight_dispatcher'
        elif post.get("selection_license_type") == 'Técnico de Mantenimiento':
            license_type = 'maintenance'
        else:
            license_type = None  # Valor predeterminado si no coincide con ninguna opción

        if post.get("selection_status") == 'Soltero(a)':
            marital = 'single'
        elif post.get("selection_status") == 'Casado(a)':
            marital = 'married'
        elif post.get("selection_status") == 'Unión Libre':
            marital = 'cohabitant'
        elif post.get("selection_status") == 'Divorciado(a)':
            marital = 'divorced'
        elif post.get("selection_status") == 'Viudo(a)':
            marital = 'widower'
        else:
            marital = 'single'  # Valor predeterminado si no coincide con ninguna opción

        vals = {
            'private_email': private_email,
            'private_phone': private_phone,
            'birthday': birthday,
            'place_of_birth': place_of_birth,
            'emergency_contact': emergency_contact,
            'relationship': relationship,
            'emergency_phone': emergency_phone,
            'country_id': int(country_id),
            'ssnid': ssnid,
            'passport_id': passport_id,
            'is_non_resident': is_non_resident,
            'resident_number': resident_number,
            'private_state_id': private_state_id,
            'private_city': private_city,
            'private_street': private_street,
            'private_street2': private_street2,
            'marital': marital,
            'children': int(children) if children else 0,
            'certificate': certificate,
            'study_field': study_field,
            'aeronatical_license': aeronatical_license,
            'license_number': license_number,
            'license_type': license_type,
            'expiration_date_license': expiration_date_license
        }

         # Copia de identidad
        identity_file = request.httprequest.files.get('identity_attachment')
        if identity_file and identity_file.filename:
            vals.update({
                'id_card': base64.b64encode(identity_file.read()),
                # 'identity_attachment_filename': identity_file.filename,
            })

        # Fotografía
        picture_file = request.httprequest.files.get('actual_picture')
        if picture_file and picture_file.filename:
            vals.update({
                'actual_picture': base64.b64encode(picture_file.read()),
                # 'actual_picture_filename': picture_file.filename,
            })

        employee_id.sudo().write(vals)

        # # --- Lógica de adjuntos ---
        # attachment_ids_to_link = []
        # for uploaded_file in uploaded_files:
        #     if uploaded_file and uploaded_file.filename:
        #         attachment_data = base64.b64encode(uploaded_file.read())
        #         # Crea el adjunto
        #         attachment = request.env['ir.attachment'].sudo().create({
        #             'name': uploaded_file.filename,
        #             'datas': attachment_data,
        #             'res_model': 'hr.leave',    # Modelo al que se adjunta
        #             'res_id': leave_id.id,      # ID del registro de la solicitud de ausencia
        #             'type': 'binary',
        #             'mimetype': uploaded_file.content_type,
        #         })
        #         attachment_ids_to_link.append(attachment.id)

        # if attachment_ids_to_link:
        #     leave_id.sudo().write({'supported_attachment_ids': [(6, 0, attachment_ids_to_link)]})

        return request.redirect('/employee/update_data')
