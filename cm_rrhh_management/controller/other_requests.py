# -*- coding: utf-8 -*-
import math
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class otherRequestPortal(http.Controller):

    @http.route('/requests_cm/other_request_cm', type='http', auth="user", website=True)
    def loan_request_option(self, **kwargs):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        places_ids = request.env['cm.business.list'].sudo().search([('business_type','=','hotel')])
        beneficiary_ids = request.env['beneficiaries.detail.list'].sudo().search([('employee_id','=',employee_id.id)])
        request_ids = request.env['rrhh.others.requests'].sudo().search([('employee_id','=',employee_id.id)])
        values = {
            'employee_name': employee_id.name,
            'places': places_ids,
            'beneficiaries': beneficiary_ids,
            'request_ids': request_ids,
        }
        return request.render("cm_rrhh_management.portal_other_request_cm", values)

    @http.route('/create_other_request/submit', type='http', auth="user", methods=["POST"], website=True)
    def create_loan_request_submit(self, **post):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        people_qty = post.get("people_qty_request")
        initial_date = post.get("initial_date_request")
        exit_date = post.get("exit_date_request")
        place_id = post.get("selection_places")
        observations = post.get("observations_request")

        vals = {
            'employee_id': employee_id.id,
            'people_qty': people_qty,
            'initial_date': initial_date,
            'exit_date': exit_date,
            'business_id': int(place_id),
            'observations': observations or ''
        }

        request_id = request.env['rrhh.others.requests'].sudo().create(vals)

        # for k, v in post.items():
        #     print("POST:", k, "=", v)

        for i in range(1, int(people_qty)+1):
            beneficiary_id = request.env['request.beneficiary'].sudo().create({
                'request_id': request_id.id,
                'beneficiary_id': int(post.get(f'beneficiary_name_{i}')),
                'employee_id': employee_id.id
            })
            beneficiary_id.sudo().data_beneficiary()
            beneficiary_id.sudo()._onchange_birth_date()

        request_id.sudo().change_business()
        request_id.sudo().get_name_date()
        request_id.sudo().with_context({'state': 'to_approve'}).change_state()

        request.session['flash_message'] = "Solicitud Ingresada con Exito"
        request.session['flash_message_type'] = 'alert-success'
        request.session.modified = True

        return request.redirect('/requests_cm/other_request_cm')