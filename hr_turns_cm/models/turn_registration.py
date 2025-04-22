from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import json
import base64
import logging

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
    ordinary_hours = fields.Float(string="Horas Totales")
    oh = fields.Float(string="HO")
    aditional_hours = fields.Float(string="Tiempo adicional")
    state = fields.Selection([('draft','Borrador'),('validated','Validado')],string="Estado",default='draft')
    editable_a = fields.Boolean(string="Editable A",default=True)
    editable_b = fields.Boolean(string="Editable B",default=True)
    fortnight_line_id = fields.Many2one('hr.fortnights.line',string="Quincena")
    note = fields.Text(string="Notas")
    validated_by_id = fields.Many2one('res.users',string="Validado por")

    def validate_day(self):
        for rec in self:
            rec.state = 'validated'
            rec.validated_by_id = self.env.user.id

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
        turn_initial_a_id = self.env['hr.options.schedules'].search([('name','=','800')])
        turn_final_a_id = self.env['hr.options.schedules'].search([('name','=','1200')])
        if self.turn_type_a.opt_turn == '0':
            self.schedule1_in_id = turn_na_id.id
            self.schedule1_out_id = turn_na_id.id
            self.editable_a = False
        else:
            if self.turn_type_a.code in ['VAC','F']:
                self.schedule1_in_id = turn_initial_a_id.id
                self.schedule1_out_id = turn_final_a_id.id
                self.editable_a = False
            else:
                self.schedule1_in_id = False
                self.schedule1_out_id = False
                self.editable_a = True
        


    @api.onchange('turn_type_b')
    def send_values_b_turn(self):
        turn_na_id = self.env['hr.options.schedules'].search([('name','=','NA')])
        turn_initial_b_id = self.env['hr.options.schedules'].search([('name','=','1300')])
        turn_final_b_id = self.env['hr.options.schedules'].search([('name','=','1700')])
        if self.turn_type_b.opt_turn == '0':
            self.schedule2_in_id = turn_na_id.id
            self.schedule2_out_id = turn_na_id.id
            self.editable_b = False
        else:
            if self.turn_type_b.code in ['VAC','F']:
                self.schedule2_in_id = turn_initial_b_id.id
                self.schedule2_out_id = turn_final_b_id.id
                self.editable_b =  False
            else:
                self.schedule2_in_id = False
                self.schedule2_out_id = False
                self.editable_b = True


    @api.onchange('schedule1_in_id','schedule1_out_id','schedule2_in_id','schedule2_out_id')
    def calculate_data(self):
        for rec in self:
            amount1 = 0
            amount2 = 0
            aditional1 = 4
            aditional2 = 4
            day = rec.date.weekday()
            try:
                amount1 = float(rec.schedule1_out_id.name) - float(rec.schedule1_in_id.name)
            except:
                amount1 = 0
                aditional1 = 0

            try:
                amount2 = float(rec.schedule2_out_id.name) - float(rec.schedule2_in_id.name)
            except:
                amount2 = 0
                aditional2 = 0


            rec.ordinary_hours = (amount1 + amount2) / 100
            if rec.ordinary_hours > 0:
                contract_id = rec.employee_id.sudo().contract_id
                if rec.date.weekday() in [5,6]:
                    rec.oh = rec.employee_id.contract_id.sudo().weekend_hours
                else:
                    rec.oh = 8

                if rec.turn_type_a.code == 'VAC' and rec.turn_type_b.code == 'LID':
                    rec.oh = amount1 / 100
                elif rec.turn_type_b.code == 'VAC' and rec.turn_type_a.code == 'LID':
                    rec.oh = amount2 / 100

                rec.aditional_hours = rec.ordinary_hours - rec.oh
            elif rec.ordinary_hours == 0:
                rec.aditional_hours = 0
                rec.oh = 0

    def get_turn_registration(self):
        actual_date = datetime.now().date()
        
        first_date = actual_date
        ult_date = actual_date + timedelta(days=6)
        actual_name = 'Semana %s al %s'%(first_date.strftime('%d/%m/%Y'), ult_date.strftime('%d/%m/%Y'))
        team_ids = self.env['hr.work.teams'].search([])
        for team in team_ids:
            name_exist = self.validate_name(team, actual_name)
            if not name_exist:
                validation = self.validate_dates(team, first_date, ult_date)
                if validation:
                    created_turn = []
                    for member in team.member_employees_ids:
                        if member.template_id:
                            count_days = 0
                            for day in range(7):
                                turn_date = actual_date + timedelta(days=count_days)
                                line_temp_id = self.get_template_line(member.template_id, day)
                                fortnight_id = self.get_fortnight(turn_date)
                                oh = 0
                                oh_value = 0
                                aditional_time = 0
                                contract_id = member.employee_id.sudo().contract_id
                                try:
                                    amount1 = float(line_temp_id.schedule1_in_id.name) - float(line_temp_id.schedule1_out_id.name)
                                    amount2 = float(line_temp_id.schedule2_in_id.name) - float(line_temp_id.schedule2_out_id.name)
                                    oh = abs((amount1 + amount2) / 100)
                                    day = turn_date.weekday()
                                    if day == 5:
                                        aditional_time = oh - 4
                                        oh_value = contract_id.sudo().weekend_hours
                                    elif day == 6:
                                        aditional_time = 0
                                        oh_value = contract_id.sudo().weekend_hours
                                    else:
                                        aditional_time = oh - 8
                                        oh_value = 8
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
                                    'oh': oh_value,
                                    'fortnight_line_id': fortnight_id.id
                                }
                                turn_id = self.create(vals)
                                created_turn.append(turn_id.id)
                                count_days += 1
                    if len(created_turn) > 0:
                        if team.send_email:
                            self.generate_and_send_report(team, actual_name)
                        self.send_mail(team, created_turn)

    def validate_name(self, team, turn):
        tuns_rec_obj =  self.env['hr.turn.registration']
        rec_ids = tuns_rec_obj.search(['|',('leader_id','=',team.leader_id.id),('responsible_id','=',team.responsible_id.id),('team_id','=',team.id)])
        if turn in set(rec_ids.mapped('name')):
            self.generate_and_send_report(team, turn)
            return True
        else:
            return False

    @api.model
    def generate_and_send_report(self, team, turn):
        user_id = team.leader_id.user_id.id
        team_id = team
        turn = turn

        notify_id = self.env['turn.email.notifications'].search([])
        emails = notify_id.line_ids.mapped('email')
        cc_email = ', '.join([noti.email for noti in notify_id.line_ids if noti.email])

        if not team_id:
            raise ValidationError("No se encontró un equipo para generar el reporte.")

        # Generar el PDF del reporte
        report_ref = 'hr_turns_cm.action_planification_format'  # Referencia del reporte
        report_action = self.env.ref(report_ref)
        pdf_content, _ = report_action._render_qweb_pdf(
            report_ref=report_ref,
            data={
            'user_id': user_id,
            'team_id': team_id.id,
            'turn': turn,
        })

        pdf_base64 = base64.b64encode(pdf_content)

        # Crear adjunto con el contenido del PDF
        pdf_name = f"Reporte_Planificacion_{fields.Date.today()}.pdf"
        attachment = self.env['ir.attachment'].create({
            'name': pdf_name,
            'type': 'binary',
            'datas': pdf_base64,
            'mimetype': 'application/pdf',
            'res_model': 'hr.turn.registration',
            'res_id': self.id,
        })

        body = """
            <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
                    <tr>
                        <td align="center">
                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">
                                <tbody>
                                    <!-- HEADER -->
                                    <tr>
                                        <td align="center" style="min-width: 590px;">
                                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                                <tr>
                                                    <td valign="middle">
                                                        <span style="font-size: 10px;">Equipo</span><br/>
                                                        {team_name}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td colspan="2" style="text-align:center;">
                                                        <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                    <!-- CONTENT -->
                                    <tr>
                                        <td align="center" style="min-width: 590px;">
                                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                                <tr>
                                                    <td valign="top" style="font-size: 13px;">
                                                        <div>
                                                            A continuacion se adjunta la planificacion para la {turn_name}
                                                            <br/>Saludos<br/>
                                                        </div>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="text-align:center;">
                                                        <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </td>
                    </tr>
                </table>
        """.format(team_name=team.name, turn_name=turn)

        # Crear y enviar correo
        mail = self.env['mail.mail'].create({
            'subject': f'Reporte de Planificación - {team.name} - {fields.Date.today()}',
            'body_html': body,
            'email_to': team.leader_id.work_email,
            'email_cc': cc_email,
            'attachment_ids': [(4, attachment.id)],
        })
        mail.send()

        _logger = logging.getLogger(__name__)
        _logger.info("####################Correo enviado con exito######################")

    def validate_dates(self, team, start_date, end_date):
        date_ranges = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        tuns_rec_obj =  self.env['hr.turn.registration']
        rec_ids = tuns_rec_obj.search(['|',('leader_id','=',team.leader_id.id),('responsible_id','=',team.responsible_id.id),('team_id','=',team.id)])
        dates = set(rec_ids.mapped('date'))
        for date in date_ranges:
            if date in dates:
                mail = self.env['mail.mail'].create({
                    'subject': "Error al crear turno",
                    'body_html': "<p>No se pudieron crear los turnos para el equipo %s por fechas ya existentes</p>"%(team.name),
                    'email_to': "oavilez@cmairlines.com",
                })
                mail.send()
                return False
        return True

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


