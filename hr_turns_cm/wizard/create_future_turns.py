# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class createFutureTurn(models.TransientModel):
    _name = 'hr.future.turns'
    _description = "Crear turnos futuros"

    @api.model
    def _get_user_default(self):
        return self.env.user.id

    start_date = fields.Date(string="Fecha de Inicio")
    end_date = fields.Date(string="Fecha Final")
    user_id = fields.Many2one('res.users',string="Usuario",default=_get_user_default)
    team_id = fields.Many2one('hr.work.teams',string="Equipo")
    line_ids = fields.One2many('hr.future.turns.lines','future_turn_id',string="Lineas")

    @api.onchange('team_id')
    def get_members(self):
        if self.line_ids:
            self.line_ids = False

        for line in self.team_id.member_employees_ids:
            vals = {
                'employee_id': line.employee_id.id,
                'turn_id': line.template_id.id,
                'team_id': self.team_id.id
            }
            self.line_ids = [(0,0,vals)]

    def create_turns(self):
        validate = self.validate_dates()
        
        actual_name = 'Semana %s al %s'%(self.start_date, self.end_date)
        created_turn = []
        for member in self.line_ids:
            count_days = 1
            for day in range(7):
                turn_date = self.start_date
                line_temp_id = self.get_template_line(member.turn_id, day)
                fortnight_id = self.get_fortnight(turn_date)
                oh = 0
                aditional_time = 0
                try:
                    amount1 = float(line_temp_id.schedule1_in_id.name) - float(line_temp_id.schedule1_out_id.name)
                    amount2 = float(line_temp_id.schedule2_in_id.name) - float(line_temp_id.schedule2_out_id.name)
                    oh = abs((amount1 + amount2) / 100)
                    day = turn_date.weekday()
                    if day == 5:
                        aditional_time = oh - 4
                    elif day == 6:
                        aditional_time = 0
                    else:
                        aditional_time = oh - 8
                except:
                    oh = 0
                vals = {
                    'employee_id': member.employee_id.id,
                    'date': turn_date,
                    'leader_id': self.team_id.leader_id.id,
                    'responsible_id': self.team_id.responsible_id.id,
                    'team_id': self.team_id.id,
                    'name': actual_name,
                    'schedule1_in_id': line_temp_id.schedule1_in_id.id,
                    'schedule1_out_id': line_temp_id.schedule1_out_id.id,
                    'schedule2_in_id': line_temp_id.schedule2_in_id.id,
                    'schedule2_out_id': line_temp_id.schedule2_out_id.id,
                    'turn_type_a': line_temp_id.turn_type_a.id,
                    'turn_type_b': line_temp_id.turn_type_b.id,
                    'ordinary_hours': oh,
                    'aditional_hours': aditional_time,
                    'fortnight_line_id': fortnight_id.id
                }
                turn_id = self.env['hr.turn.registration'].create(vals)
                created_turn.append(turn_id.id)
                count_days += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Exito",
                'type': 'success',
                'message': "Turnos creados correctamente",
                'sticky': False
            },
            'next': {
                'type': 'ir.actions.act_window_close'
            }
        }

    def get_template_line(self, template_id, day):
        tmp_line_id = template_id.template_line_ids.filtered(lambda line: line.day_opt == str(day))
        return tmp_line_id

    def get_fortnight(self, date):
        id_fortnight = self.env['hr.fortnights'].search([('actual','=',True)])
        line_id = id_fortnight.line_ids.filtered(lambda line_f: line_f.start_date <= date and line_f.end_date >= date)
        return line_id

    def validate_dates(self):
        diff_days = (self.end_date - self.start_date).days + 1
        if self.start_date > self.end_date:
            raise ValidationError('La fecha de inicio no puede ser mayor que la final.')

        if diff_days != 7:
            raise ValidationError('Solo se pueden crear turnos de 7 dias.')

        date_ranges = [self.start_date + timedelta(days=i) for i in range((self.end_date - self.start_date).days + 1)]
        tuns_rec_obj =  self.env['hr.turn.registration']
        rec_ids = tuns_rec_obj.search(['|',('leader_id.user_id','=',self.user_id.id),('responsible_id.user_id','=',self.user_id.id),('team_id','=',self.team_id.id)])
        dates = set(rec_ids.mapped('date'))
        for date in date_ranges:
            if date in dates:
                raise ValidationError("La fecha %s ya esta registrada en un turno ya creado para el equipo %s"%(date, self.team_id.name))
        return True


class linesFutureTurn(models.TransientModel):
    _name = 'hr.future.turns.lines'
    _description = "Lineas turnos futuros"

    future_turn_id = fields.Many2one('hr.future.turns',string="Turno Futuro")
    employee_id = fields.Many2one('hr.employee',string="Empleado")
    turn_id = fields.Many2one('hr.templates.turn',string="Turno")
    team_id = fields.Many2one('hr.work.teams',string="Equipo")