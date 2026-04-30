from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class CustomPortalReserveRoom(http.Controller):

    @http.route('/reserveroom/record_reserve_room', type='http', auth="user", website=True)
    def reserve_room(self, **kwargs):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        employee_company_id = employee_id.company_id.id
        return request.render("portal_cm.reserve_room_portal")


    @http.route('/request_reserve/submit', type='http', auth="user", methods=["POST"], website=True)
    def request_reserve_submit(self, **post):
        user = request.env.user
        company_id = request.env.user.company_id
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        if not employee_id:
            return "Error: No se encontró un empleado vinculado a este usuario. Verifique su configuración en Odoo."

        consult_date = post.get("consult_date")
        consult_initial_date = datetime.strptime(consult_date, "%Y-%m-%d")
        consult_final_date = datetime.strptime(consult_date, "%Y-%m-%d") + timedelta(hours=23)
        reserve_ids = request.env['room.booking'].sudo().search([('start_datetime','>=',consult_initial_date),('start_datetime','<=',consult_final_date)])
        return request.render("portal_cm.reserve_room_portal", {
            'reserve_ids': reserve_ids,
        })

    @http.route('/request_create_reserve/submit', type='http', auth="user", methods=["POST"], website=True)
    def request_create_reserve_submit(self, **post):
        user = request.env.user
        company_id = request.env.user.company_id
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        room_id = request.env['room.room'].sudo().search([('short_code','=','xcala01')], limit=1)
        if not employee_id:
            return "Error: No se encontró un empleado vinculado a este usuario. Verifique su configuración en Odoo."

        if not room_id:
            return "Error: no existe sala con codigo xcala01."
        
        initial_date = post.get("initial_date")
        end_date = post.get("final_date")
        reserve_name = post.get("record_reserve_name")

        start_date = datetime.strptime(initial_date, "%Y-%m-%dT%H:%M") + timedelta(hours=6)
        final_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M") + timedelta(hours=6)

        vals = {
            'organizer_id': employee_id.user_id.id,
            'name': reserve_name,
            'room_id': room_id.id,
            'start_datetime': start_date,
            'stop_datetime': final_date
        }
        reserve_id = request.env['room.booking'].sudo().create(vals)        
        if reserve_id:
            request.session['flash_message'] = 'Reserva de sala creada correctamente'
            request.session['flash_message_type'] = 'alert-success'
        return request.redirect('/reserveroom/record_reserve_room')