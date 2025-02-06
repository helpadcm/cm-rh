from odoo import http
from odoo.http import request
from datetime import datetime, timedelta

class CustomPortal(http.Controller):

    @http.route('/turns/record_hours_team', type='http', auth="user", website=True)
    def custom_option(self, **kwargs):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        types_turn_ids = request.env['hr.turn.types'].sudo().search([])
        schedule_ids = request.env['hr.options.schedules'].sudo().search([('alphabetical','=',False)])
        draft_record_ids = request.env['team.hour.record'].sudo().search([('employee_id','=',employee_id.id)], order="date desc")
        validate_record_ids = request.env['hr.turn.registration'].sudo().search([('employee_id','=',employee_id.id),('state','=','validated')], order="date desc")
        return request.render("portal_cm.portal_hours_record_team", {"records": types_turn_ids, "schedules": schedule_ids, 'draft_hours': draft_record_ids, 'validate_records': validate_record_ids})

    @http.route('/clear_flash_message', type='http', auth="user", methods=["POST"], website=True)
    def clear_flash_message(self):
        request.session['flash_message'] = None
        request.session.modified = True
        return 'OK'

    @http.route('/hours_day_record/submit', type='http', auth="user", methods=["POST"], website=True)
    def hours_form_submit(self, **post):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)

        member_team_id = request.env['hr.employees.members'].sudo().search([('employee_id','=',employee_id.id)])

        date = post.get("date_record")

        exist_rec_id = request.env['team.hour.record'].sudo().search([('date','=',date),('employee_id','=',employee_id.id)])
        if not exist_rec_id:
            name_week = self.get_week_name(date)

            type_a_value = post.get("selection_turn_type_a")
            entry_1_value = post.get("rec_entry_1")
            out_1_value = post.get("rec_out_1")

            type_b_value = post.get("selection_turn_type_b")
            entry_2_value = post.get("rec_entry_2")
            out_2_value = post.get("rec_out_2")

            notes = post.get('record_notes') or ''

            if all([date, type_a_value, entry_1_value, out_1_value, type_b_value, entry_2_value, out_2_value]):
                entry_1_id = request.env['hr.options.schedules'].sudo().search([('id','=',entry_1_value)])
                out_1_id = request.env['hr.options.schedules'].sudo().search([('id','=',out_1_value)])

                entry_2_id = request.env['hr.options.schedules'].sudo().search([('id','=',entry_2_value)])
                out_2_id = request.env['hr.options.schedules'].sudo().search([('id','=',out_2_value)])

                type_turn_a_id = request.env['hr.turn.types'].sudo().search([('id','=',type_a_value)])
                type_turn_b_id = request.env['hr.turn.types'].sudo().search([('id','=',type_b_value)])

                vals = {
                    'name': name_week,
                    'employee_id': employee_id.id,
                    'team_id': member_team_id.team_id.id,
                    'leader_id': member_team_id.team_id.leader_id.id,
                    'responsible_id': member_team_id.team_id.responsible_id.id,
                    'date': date,
                    'schedule1_in_id': entry_1_id.id,
                    'schedule1_out_id': out_1_id.id,
                    'turn_type_a': type_turn_a_id.id,
                    'schedule2_in_id': entry_2_id.id,
                    'schedule2_out_id': out_2_id.id,
                    'turn_type_b': type_turn_b_id.id,
                    'note': notes
                }
                rec_id = request.env['team.hour.record'].sudo().create(vals)
                rec_id.sudo().send_values_a_turn()
                rec_id.sudo().send_values_b_turn()
                rec_id.sudo().calculate_data()

                request.session['flash_message'] = '¡Horas registradas correctamente!'
                request.session['flash_message_type'] = 'alert-success'
                request.session.modified = True
            else:
                request.session['flash_message'] = 'Hubo un error al registrar las horas, por favor revise los datos.'
                request.session['flash_message_type'] = 'alert-danger'
                request.session.modified = True
        else:
            date_format = datetime.strptime(date, '%Y-%m-%d')
            request.session['flash_message'] = 'Ya existen registros para la fecha %s.'%(date_format.strftime("%d/%m/%Y"))
            request.session['flash_message_type'] = 'alert-danger'
            request.session.modified = True

        return request.redirect('/turns/record_hours_team')

    @http.route('/delete_record/<int:day_id>', type="http", auth="user", methods=["POST"], website=True)
    def delete_record(self, day_id, **kwargs):
        day_rec_id = request.env['team.hour.record'].sudo().search([('id','=',day_id)])
        if day_rec_id:
            day_rec_id.sudo().unlink()
        return request.redirect('/turns/record_hours_team') 


    def get_week_name(self, date):
        date_format = datetime.strptime(date, '%Y-%m-%d')
        initial_date = date_format - timedelta(days=date_format.weekday())
        end_date = initial_date + timedelta(days=6)
        week_name = 'Semana %s al %s'%(initial_date.strftime('%d/%m/%Y'), end_date.strftime('%d/%m/%Y'))
        return week_name