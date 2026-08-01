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
        state_ids = request.env['res.country.state'].sudo().search([])
        values = {
            'private_email': employee_id.private_email,
            'private_phone': employee_id.private_phone,
            'complete_name': employee_id.legal_name,

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

            'state_ids': state_ids,
            'state_id': employee_id.private_state_id.id,
            'city': employee_id.private_city,
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