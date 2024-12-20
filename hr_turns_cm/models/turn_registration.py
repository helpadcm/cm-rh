from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import json

class turnRegistration(models.Model):
    _name = 'hr.turn.registration'
    _description = 'Turnos: Registro de turnos'

    name = fields.Char(string='Nombre')
    leader_id = fields.Many2one('hr.employee',string="Lider de Equipo")
    responsible_id = fields.Many2one('hr.employee',string="Responsable de Equipo")
    employee_id = fields.Many2one('hr.employee',string="Empleado")
    date = fields.Date(string="Fecha")
    team_id = fields.Many2one('hr.work.teams',string="Equipo")
    schedule1_in_id = fields.Many2one('hr.options.schedules',string="Entrada 1")
    schedule1_out_id = fields.Many2one('hr.options.schedules',string="Salida 1")
    schedule2_in_id = fields.Many2one('hr.options.schedules',string="Entrada 2")
    schedule2_out_id = fields.Many2one('hr.options.schedules',string="Salida 2")
    ordinary_hours = fields.Float(string="HO Laboradas")
    aditional_hours = fields.Float(string="Tiempo adicional")
    state = fields.Selection([('draft','Borrador'),('validated','Validado')],string="Estado",default='draft')

    @api.onchange('schedule1_in_id','schedule1_out_id','schedule2_in_id','schedule2_out_id')
    def calculate_data(self):
        for rec in self:
            try:
                amount1 = float(rec.schedule1_out_id.name) - float(rec.schedule1_in_id.name)
                amount2 = float(rec.schedule2_out_id.name) - float(rec.schedule2_in_id.name)
                rec.ordinary_hours = (amount1 + amount2) / 100
                day = rec.date.weekday()
                if day == 5:
                    rec.aditional_hours = rec.ordinary_hours - 4
                elif day == 6:
                    rec.aditional_hours = 0
                else:
                    rec.aditional_hours = rec.ordinary_hours - 8
            except:
                rec.ordinary_hours = 0
                rec.aditional_hours = 0

    def get_turn_registration(self):
        actual_date = datetime.now().date()

        last_date = actual_date - timedelta(days=6)
        ult_last_date = actual_date
        
        first_date = actual_date + timedelta(days=1)
        ult_date = actual_date + timedelta(days=7)
        
        actual_name = 'Semana %s al %s'%(first_date, ult_date)
        last_name = 'Semana %s al %s'%(last_date, ult_last_date)
        
        last_turns_ids = self.env['hr.turn.registration'].search([('name','=',last_name)])
        team_ids = self.env['hr.work.teams'].search([])
        if len(last_turns_ids) == 0:
            for team in team_ids:
                created_turn = []
                for member in team.members_ids:
                    count_days = 1
                    for day in range(7):
                        turn_date = actual_date + timedelta(days=count_days)
                        vals = {
                            'employee_id': member.id,
                            'date': turn_date,
                            'leader_id': team.leader_id.id,
                            'responsible_id': team.responsible_id.id,
                            'team_id': team.id,
                            'name': actual_name
                        }
                        turn_id = self.create(vals)
                        created_turn.append(turn_id.id)
                        count_days += 1
                if len(created_turn) > 0:
                    self.send_mail(team, created_turn)
        else:
            for team in team_ids:
                lines_teams_ids = last_turns_ids.filtered(lambda turn: turn.team_id.id == team.id)
                created_turn = []
                for member in team.members_ids:
                    turn_ids = lines_teams_ids.filtered(lambda emp: emp.employee_id.id == member.id)
                    count_days = 1
                    if turn_ids:
                        for day in range(7):
                            turn_date = actual_date + timedelta(days=count_days)
                            oh = 0
                            try:
                                amount1 = float(turn_ids[day].schedule1_in_id.name) - float(turn_ids[day].schedule1_out_id.name)
                                amount2 = float(turn_ids[day].schedule2_in_id.name) - float(turn_ids[day].schedule2_out_id.name)
                                oh = (amount1 + amount2) / 100
                            except:
                                oh = 0

                            vals = {
                                'employee_id': member.id,
                                'date': turn_date,
                                'leader_id': team.leader_id.id,
                                'responsible_id': team.responsible_id.id,
                                'team_id': team.id,
                                'name': actual_name,
                                'schedule1_in_id': turn_ids[day].schedule1_in_id.id,
                                'schedule1_out_id': turn_ids[day].schedule1_out_id.id,
                                'schedule2_in_id': turn_ids[day].schedule2_in_id.id,
                                'schedule2_out_id': turn_ids[day].schedule2_out_id.id,
                                'ordinary_hours': oh
                            }
                            turn_id = self.create(vals)
                            created_turn.append(turn_id.id)
                            count_days += 1
                if len(created_turn) > 0:
                    self.send_mail(team, created_turn)

    def send_mail(self, team, list_turns):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        domain = [('id', 'in', list_turns)]
        domain_json = json.dumps(domain)
        action_id = self.env.ref('hr_turns_cm.action_turn_registration')
        base_url += '/web#action=%s&model=%s&view_type=list&domain=%s' % (
            action_id.id,
            self._name,
            domain_json
        )
        template_id = self.env.ref('hr_turns_cm.review_turns_template')
        template_ctx = {
            'action_url': base_url,
            'email_to': team.responsible_id.work_email,
            'responsible': team.responsible_id.name,
            'team': team.name,
        }
        template_id.with_context(**template_ctx).send_mail(self.id, force_send=True)


