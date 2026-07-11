# -*- coding: utf-8 -*-
import math
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class loanRequestPortal(http.Controller):

    @http.route('/requests_cm/loan_request_cm', type='http', auth="user", website=True)
    def loan_request_option(self, **kwargs):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        request_ids = request.env['rrhh.request.loan'].sudo().search([('employee_id','=',employee_id.id)])
        days = (datetime.now().date() - employee_id.contract_date_start).days
        years = math.floor(days/365)
        show_form = 'allow'
        messsage_form = ''
        if request_ids:
            last_request_id = request_ids[len(request_ids) - 1]
            if last_request_id.state == 'finalized':
                months = (datetime.now().date() - last_request_id.deduction_id.date_estimated_end).days / 30
                if months < 6:
                    show_form = 'not_allow'
                    messsage_form = f"""No tiene permiso para solicitar prestamos, debe tener al menos 6 meses desde su ultima solicitud. 
                            Su ultima solicitud finaliza el {last_request_id.deduction_id.date_estimated_end.strftime("%d/%m/%Y")} 
                            intente de nuevo a partir del {(last_request_id.deduction_id.date_estimated_end + relativedelta(months=6)).strftime("%d/%m/%Y")}"""
            elif last_request_id.state in ['pending','approved','assessment','finance','payroll']:
                messsage_form = 'Su ultima solicitud se encuentra en proceso, podra solicitar hasta que se complete.'
                show_form = 'not_allow'
            elif last_request_id.state in ['waiting']:
                messsage_form = f"""Ya cuenta con una solicitud "EN ESPERA" con fecha estimada para el {last_request_id.estimated_date.strftime("%d/%m/%Y")}."""
                show_form = 'not_allow'


        if years < 1:
            show_form = False
            messsage_form = 'No tiene permiso para solicitar prestamos, debe tener minimo 1 año de antiguedad.'

        values = {
            'employee_name': employee_id.name,
            'income_date': employee_id.contract_date_start,
            'seniority': employee_id.seniority,
            'years_old': years,
            'historical_request': request_ids,
            'show_form': show_form,
            'messsage_form': messsage_form
        }
        return request.render("cm_rrhh_management.portal_loan_request_cm", values)

    @http.route('/create_loan_request/submit', type='http', auth="user", methods=["POST"], website=True)
    def create_loan_request_submit(self, **post):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        amount = post.get("amount_request")
        fees = post.get("selection_fees")
        reason = post.get("reason_request")
        vals = {
            'employee_id': employee_id.id,
            'amount': amount,
            'reason': reason,
            'fees': fees
        }

        request_id = request.env['rrhh.request.loan'].sudo().create(vals)
        request_id.sudo().get_employee_data()
        request_id.sudo().calculate_amounts()
        request_id.sudo().with_context({'state': 'assessment'}).change_state()

        request.session['flash_message'] = "Solicitud Ingresada con Exito"
        request.session['flash_message_type'] = 'alert-success'

        return request.redirect('/requests_cm/loan_request_cm')