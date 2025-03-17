from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

second = [26,27,28,29,30,31,1,2,3,4,5,6,7,8,9,10]
first = [11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]

class CustomPortal(http.Controller):

    @http.route('/turns/record_hours_team', type='http', auth="user", website=True)
    def custom_option(self, **kwargs):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        types_turn_ids = request.env['hr.turn.types'].sudo().search([])
        schedule_ids = request.env['hr.options.schedules'].sudo().search([('alphabetical','=',False)])
        draft_record_ids = request.env['team.hour.record'].sudo().search([('employee_id','=',employee_id.id)], order="date desc")
        turn_na_id = request.env['hr.options.schedules'].sudo().search([('name','=','NA')])

        turn_initial_a_id = request.env['hr.options.schedules'].sudo().search([('name','=','800')])
        turn_final_a_id = request.env['hr.options.schedules'].sudo().search([('name','=','1200')])
        turn_initial_b_id = request.env['hr.options.schedules'].sudo().search([('name','=','1300')])
        turn_final_b_id = request.env['hr.options.schedules'].sudo().search([('name','=','1700')])

        actual_date = datetime.now() - timedelta(hours=6)
        
        domain = [('employee_id','=',employee_id.id),('state','=','validated')]
        actual_domain = [('employee_id','=',employee_id.id),('state','=','validated')]

        if actual_date.day in first:
            min_date = actual_date.replace(day=11).date() - relativedelta(months=1)
            max_date = actual_date.replace(day=25).date() - relativedelta(months=1)
            domain.extend([('date','>=',min_date),('date','<=',max_date)])

            actual_min_date = actual_date.replace(day=26).date() - relativedelta(months=1)
            actual_max_date = actual_date.replace(day=10).date()
            actual_domain.extend([('date','>=',actual_min_date),('date','<=',actual_max_date)])

        elif actual_date.day in second:
            min_date = actual_date.replace(day=26).date() - relativedelta(months=1)
            max_date = actual_date.replace(day=10).date()
            domain.extend([('date','>=',min_date),('date','<=',max_date)])

            actual_min_date = actual_date.replace(day=11).date()
            actual_max_date = actual_date.replace(day=25).date()
            actual_domain.extend([('date','>=',actual_min_date),('date','<=',actual_max_date)])
        
        validate_record_ids = request.env['hr.turn.registration'].sudo().search(domain, order="date desc")
        actual_record_ids = request.env['hr.turn.registration'].sudo().search(actual_domain, order="date desc")
        values = {
            "records": types_turn_ids, 
            "schedules": schedule_ids, 
            'draft_hours': draft_record_ids, 
            'validate_records': validate_record_ids, 
            'turn_na_id': turn_na_id.id, 
            'turn_initial_a_id' : turn_initial_a_id.id,
            'turn_final_a_id' : turn_final_a_id.id,
            'turn_initial_b_id' : turn_initial_b_id.id,
            'turn_final_b_id' : turn_final_b_id.id,
            'actual_record_ids': actual_record_ids
        }
        return request.render("portal_cm.portal_hours_record_team", values)

    @http.route('/clear_flash_message', type='http', auth="user", methods=["POST"], website=True)
    def clear_flash_message(self):
        request.session['flash_message'] = None
        request.session.modified = True
        return 'OK'

    @http.route('/hours_day_record/submit', type='http', auth="user", methods=["POST"], website=True)
    def hours_form_submit(self, **post):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        turn_na_id = request.env['hr.options.schedules'].sudo().search([('name','=','NA')])
        turn_initial_a_id = request.env['hr.options.schedules'].sudo().search([('name','=','800')])
        turn_final_a_id = request.env['hr.options.schedules'].sudo().search([('name','=','1200')])
        turn_initial_b_id = request.env['hr.options.schedules'].sudo().search([('name','=','1300')])
        turn_final_b_id = request.env['hr.options.schedules'].sudo().search([('name','=','1700')])

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

            def_entry_1_value = post.get("initial_turn_a")
            def_out_1_value = post.get("final_turn_a")
            def_entry_2_value = post.get("initial_turn_b")
            def_out_2_value = post.get("final_turn_b")

            notes = post.get('record_notes') or ''

            type_turn_a_id = request.env['hr.turn.types'].sudo().search([('id','=',type_a_value)])
            type_turn_b_id = request.env['hr.turn.types'].sudo().search([('id','=',type_b_value)])
            validator = True
            vals = {
                'name': name_week,
                'employee_id': employee_id.id,
                'team_id': member_team_id.team_id.id,
                'leader_id': member_team_id.team_id.leader_id.id,
                'responsible_id': member_team_id.team_id.responsible_id.id,
                'date': date,
                'turn_type_a': type_turn_a_id.id,
                'turn_type_b': type_turn_b_id.id,
                'note': notes
            }
            if type_turn_a_id.opt_turn == '0' and type_turn_b_id.opt_turn == '1':
                entry_2_id = request.env['hr.options.schedules'].sudo().search([('id','=',entry_2_value)])
                out_2_id = request.env['hr.options.schedules'].sudo().search([('id','=',out_2_value)])
                validator = self.validate_hours(None, None, entry_2_id.name, out_2_id.name, type_turn_a_id.code, type_turn_b_id.code)    
                vals.update({
                    'schedule1_in_id': turn_na_id.id,
                    'schedule1_out_id': turn_na_id.id,
                    'schedule2_in_id': entry_2_id.id,
                    'schedule2_out_id': out_2_id.id,
                })
            
            elif type_turn_a_id.opt_turn == '1' and type_turn_b_id.opt_turn == '0':
                entry_1_id = request.env['hr.options.schedules'].sudo().search([('id','=',entry_1_value)])
                out_1_id = request.env['hr.options.schedules'].sudo().search([('id','=',out_1_value)])
                validator = self.validate_hours(entry_1_id.name, out_1_id.name, None, None, type_turn_a_id.code, type_turn_b_id.code)
                vals.update({
                    'schedule1_in_id': entry_1_id.id,
                    'schedule1_out_id': out_1_id.id,
                    'schedule2_in_id': turn_na_id.id,
                    'schedule2_out_id': turn_na_id.id,
                })
            elif type_turn_a_id.opt_turn == '0' and type_turn_b_id.opt_turn == '0':
                vals.update({
                    'schedule1_in_id': turn_na_id.id,
                    'schedule1_out_id': turn_na_id.id,
                    'schedule2_in_id': turn_na_id.id,
                    'schedule2_out_id': turn_na_id.id,
                })
            else:
                entry_1_id = request.env['hr.options.schedules'].sudo().search([('id','=',entry_1_value)])
                out_1_id = request.env['hr.options.schedules'].sudo().search([('id','=',out_1_value)])
                entry_2_id = request.env['hr.options.schedules'].sudo().search([('id','=',entry_2_value)])
                out_2_id = request.env['hr.options.schedules'].sudo().search([('id','=',out_2_value)])
                print ("################################")
                print (entry_1_id.name, out_1_id.name, entry_2_id.name, out_2_id.name, type_turn_a_id.code, type_turn_b_id.code)
                validator = self.validate_hours(entry_1_id.name, out_1_id.name, entry_2_id.name, out_2_id.name, type_turn_a_id.code, type_turn_b_id.code)
                vals.update({
                    'schedule1_in_id': entry_1_id.id,
                    'schedule1_out_id': out_1_id.id,
                    'schedule2_in_id': entry_2_id.id,
                    'schedule2_out_id': out_2_id.id,
                })

            if validator:
                rec_id = request.env['team.hour.record'].sudo().create(vals)
                rec_id.sudo().send_values_a_turn()
                rec_id.sudo().send_values_b_turn()
                rec_id.sudo().calculate_data()

                request.session['flash_message'] = '¡Horas registradas correctamente!'
                request.session['flash_message_type'] = 'alert-success'
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

    def validate_hours(self, entry1, out1, entry2, out2, code_a, code_b):
        print ("/////////////////////////")
        print (code_a, code_b)
        if all([entry1, out1, entry2, out2]):
            entry1_value = float(entry1)
            out1_value = float(out1)
            entry2_value = float(entry2)
            out2_value = float(out2)
            if entry1_value < out1_value < entry2_value < out2_value:
                return True
            else:
                messages = []
                if not entry1_value < out1_value:
                    messages.append("Error: La salida 1 no puede ser menor que la entrada 1")
                if not out1_value < entry2_value:
                    messages.append("Error: La entrada 2 no puede ser menor que la salida 1")
                if not entry2_value < out2_value:
                    messages.append("Error: La salida 2 no puede ser menor que la entrada 2")
                if not out2_value > max(entry1_value, out1_value, entry2_value):
                    messages.append("Error: La salida 2 debe ser mayor que todos.")

                request.session['flash_message'] = "\n".join(messages)
                request.session['flash_message_type'] = 'alert-danger'
                request.session.modified = True
                return False

        elif not entry1 and not out1:
            entry2_value = float(entry2)
            out2_value = float(out2)
            print (entry2_value, out2_value)
            if entry2_value < out2_value:
                return True
            else:
                messages = []
                if not entry2_value < out2_value:
                    messages.append("Error: La salida 2 no puede ser menor que la entrada 2")

                request.session['flash_message'] = "\n".join(messages)
                request.session['flash_message_type'] = 'alert-danger'
                request.session.modified = True
                return False

        elif not entry2 and not out2:
            entry1_value = float(entry1)
            out1_value = float(out1)
            if entry1_value < out1_value:
                return True
            else:
                messages = []
                if not entry1_value < out1_value:
                    messages.append("Error: La salida 1 no puede ser menor que la entrada 1")

                request.session['flash_message'] = "\n".join(messages)
                request.session['flash_message_type'] = 'alert-danger'
                request.session.modified = True
                return False