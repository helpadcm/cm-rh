from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import json

week_days = ['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo']

class turnRegistration(models.Model):
    _name = 'hr.turn.registration'
    _description = 'Turnos: Registro de turnos'

    @api.model
    def _get_default_type(self):
        type_id =  self.env['hr.turn.types'].search([('default_turn','=',True)])
        return type_id.id

    name = fields.Char(string='Nombre')
    leader_id = fields.Many2one('hr.employee',string="Lider de Equipo")
    responsible_id = fields.Many2one('hr.employee',string="Responsable de Equipo")
    employee_id = fields.Many2one('hr.employee',string="Empleado")
    date = fields.Date(string="Fecha")
    name_day = fields.Char(string="Dia", compute="get_day_name")
    team_id = fields.Many2one('hr.work.teams',string="Equipo")
    schedule1_in_id = fields.Many2one('hr.options.schedules',string="Entrada 1")
    schedule1_out_id = fields.Many2one('hr.options.schedules',string="Salida 1")
    turn_type_a = fields.Many2one('hr.turn.types',string="Tipo Turno A", default=_get_default_type)
    schedule2_in_id = fields.Many2one('hr.options.schedules',string="Entrada 2")
    schedule2_out_id = fields.Many2one('hr.options.schedules',string="Salida 2")
    turn_type_b = fields.Many2one('hr.turn.types',string="Tipo Turno B", default=_get_default_type)
    ordinary_hours = fields.Float(string="HO Laboradas")
    aditional_hours = fields.Float(string="Tiempo adicional")
    state = fields.Selection([('draft','Borrador'),('validated','Validado')],string="Estado",default='draft')
    editable_a = fields.Boolean(string="Editable A",default=True)
    editable_b = fields.Boolean(string="Editable B",default=True)
    fortnight_line_id = fields.Many2one('hr.fortnights.line',string="Quincena")

    @api.depends('date')
    def get_day_name(self):
        for rec in self:
            if rec.date:
                rec.name_day = week_days[rec.date.weekday()]
            else:
                rec.name_day = ''

    @api.onchange('turn_type_a')
    def send_values_a_turn(self):
        turn_na_id = self.env['hr.options.schedules'].search([('name','=','NA')])
        domain = [('alphabetical','=',False)]
        if self.turn_type_a.opt_turn == '0':
            domain = [('alphabetical','=',True)]
            self.schedule1_in_id = turn_na_id.id
            self.schedule1_out_id = turn_na_id.id
            self.editable_a = False
        else:
            self.schedule1_in_id = False
            self.schedule1_out_id = False
            self.editable_a = True
        return {'domain': {'schedule1_in_id': domain, 'schedule1_out_id': domain}}

    @api.onchange('turn_type_b')
    def send_values_b_turn(self):
        turn_na_id = self.env['hr.options.schedules'].search([('name','=','NA')])
        domain = [('alphabetical','=',False)]
        if self.turn_type_b.opt_turn == '0':
            self.schedule2_in_id = turn_na_id.id
            self.schedule2_out_id = turn_na_id.id
            self.editable_b = False
        else:
            self.schedule2_in_id = False
            self.schedule2_out_id = False
            self.editable_b = True
        return {'domain': {'schedule2_in_id': domain, 'schedule2_out_id': domain}}

    @api.onchange('schedule1_in_id','schedule1_out_id','schedule2_in_id','schedule2_out_id')
    def calculate_data(self):
        for rec in self:
            amount1 = 0
            amount2 = 0
            day = rec.date.weekday()
            try:
                amount1 = float(rec.schedule1_out_id.name) - float(rec.schedule1_in_id.name)
            except:
                amount1 = 0

            try:
                amount2 = float(rec.schedule2_out_id.name) - float(rec.schedule2_in_id.name)
            except:
                amount2 = 0

            rec.ordinary_hours = (amount1 + amount2) / 100
            if day == 5:
                rec.aditional_hours = rec.ordinary_hours - 4
            elif day == 6:
                rec.aditional_hours = 0
            else:
                rec.aditional_hours = rec.ordinary_hours - 8

    def get_turn_registration(self):
        actual_date = datetime.now().date()
        
        first_date = actual_date + timedelta(days=1)
        ult_date = actual_date + timedelta(days=7)
        
        actual_name = 'Semana %s al %s'%(first_date, ult_date)
        
        team_ids = self.env['hr.work.teams'].search([])
        for team in team_ids:
            created_turn = []
            for member in team.member_employees_ids:
                count_days = 1
                for day in range(7):
                    turn_date = actual_date + timedelta(days=count_days)
                    line_temp_id = self.get_template_line(member.template_id, day)
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
                        'leader_id': team.leader_id.id,
                        'responsible_id': team.responsible_id.id,
                        'team_id': team.id,
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
                    turn_id = self.create(vals)
                    created_turn.append(turn_id.id)
                    count_days += 1
            if len(created_turn) > 0:
                self.send_mail(team, created_turn)

    def get_fortnight(self, date):
        id_fortnight = self.env['hr.fortnights'].search([('actual','=',True)])
        line_id = id_fortnight.line_ids.filtered(lambda line_f: line_f.start_date <= date and line_f.end_date >= date)
        return line_id

    def get_template_line(self, template_id, day):
        tmp_line_id = template_id.template_line_ids.filtered(lambda line: line.day_opt == str(day))
        return tmp_line_id

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


