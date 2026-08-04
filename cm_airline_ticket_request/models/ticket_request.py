# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime
import json

class ticket_request(models.Model):    
    _name = 'cm.ticket.request'
    _description = "Solicitud de boletos"
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = "name desc"

    @api.model
    def _get_default_date(self):
        return datetime.now().date()

    @api.model
    def user_default(self):
        return self.env.user.id

    @api.model
    def default_get(self, fields):
        rec = super(ticket_request, self).default_get(fields)
        program_default_id = self.env['cm.ticket.request.program'].search([('default_program','=',True)])
        airline_default_id = self.env['cm.ticket.request.airline'].search([('default_airline','=',True)])
        if program_default_id:
            rec.update({
                'program_id': program_default_id[0].id
            })
        if airline_default_id:
            rec.update({
                'airline_id': airline_default_id[0].id
            })
        return rec

    name = fields.Char(string="Numero", default="Borrador", tracking=True, copy=False)
    user_id = fields.Many2one('res.users',string="Solicitante",default=user_default)
    assigned_user_id = fields.Many2one('res.users',string="Asignado a", copy= False,tracking=True)
    date = fields.Date(string="Fecha de Creacion", default=_get_default_date)
    request_date = fields.Date(string="Fecha de Solicitud", tracking=True)
    request_type = fields.Selection([('round_trip','Ida y Vuelta'),('exit_only','Solo Ida'),('multiple','Multiple')],string="Tipo de Solicitud", default="round_trip", tracking=True,copy=True)
    state = fields.Selection([('draft','Borrador'),('send','Enviado'),('received','Recibido'),('finalized','Finalizado'),('canceled','Cancelado')], string="Estado", default='draft', tracking=True,copy=False)
    program_id = fields.Many2one('cm.ticket.request.program',string="Programa",copy=True,tracking=True)
    list_request_ids = fields.One2many('cm.ticket.request.line','request_id',string="Listado",copy=True)
    list_routes_ids = fields.One2many('cm.routes.line','request_id',string="Listado Rutas",copy=True)
    only_pnr = fields.Boolean(string="Unico PNR",copy=False)
    pnr = fields.Char(string="PNR",copy=False)
    notifications_select = fields.Selection([('applicant','Solicitante'),('passengers','Pasajeros')],default="applicant",string="Notificar a",tracking=True)
    pnr_file = fields.Binary(string="Doc PNR",copy=False)
    pnr_file_name = fields.Char(string="Nombre PNR",copy=False,tracking=True)
    airline_id = fields.Many2one('cm.ticket.request.airline',string="Aerolinea",copy=True,tracking=True)
    ticket_type_request = fields.Selection(string="Tipo de solicitud de boleto",related="airline_id.ticket_type_request")

    @api.onchange('pnr')
    def change_pnr(self):
        if self.pnr:
            self.list_request_ids.write({'pnr': self.pnr})

    @api.onchange('list_routes_ids')
    def _recompute_sequence(self):
        for index, line in enumerate(self.list_routes_ids.sorted(key=lambda l: l.id or 0), start=1):
            if index % 2 != 0:
                line.ticket_type = 'one_way'
            else:
                line.ticket_type = 'return'
            line.sequence = index

    def change_state(self):
        next_state = self.env.context.get('state')
        if next_state == 'send':
            self.validate_send()
            if self.name == 'Borrador':
                sequence_id = self.env.ref('cm_airline_ticket_request.sequence_ticket_request_cm')
                self.name = sequence_id.next_by_id()
                self.send_request_mail()

        if next_state == 'received':
            self.assigned_user_id = self.env.user.id

        if next_state == 'finalized':
            self.validate_finalize()
            self.send_finalize_mail()
        self.state = next_state

    def validate_finalize(self):
        if not self.only_pnr:
            for line in self.list_request_ids:
                if not line.pnr_file:
                    raise ValidationError(f"""Debe adjuntar el documento del pasajero {line.name}""")
        else:
            if not self.pnr_file:
                raise ValidationError("Debe adjuntar el documento")

    def validate_send(self):
        if len(self.list_routes_ids) == 0:
            raise ValidationError("No hay rutas ingresadas a la solicitud")

        if len(self.list_request_ids) == 0:
            raise ValidationError("No hay pasajeros ingresados a la solicitud")

        if self.request_type == 'round_trip':
            if len(self.list_routes_ids) != 2:
                raise ValidationError("Si el tipo de solicitud es de Ida y Vuelta debe agregar dos rutas")
            
            line1_id = self.list_routes_ids[0].route_id
            line2_id = self.list_routes_ids[1].route_id
            if line1_id.destination != line2_id.origin:
                raise ValidationError(f"Si su solicitud es de Ida y Vuelta el destino de su primera ruta ({line1_id.destination}) debe coincidir con el origen de la segunda ({line2_id.origin})")

            if line2_id.destination != line1_id.origin:
                raise ValidationError(f"Si su solicitud es de Ida y Vuelta el destino de su segunda ruta ({line2_id.destination}) debe coincidir con el origen de la primera ({line1_id.origin})")

        elif self.request_type == 'exit_only':
            if len(self.list_routes_ids) != 1:
                raise ValidationError("Si el tipo de solicitud es Solo de Ida debe agregar una ruta")

    def send_request_mail(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        domain = [('id', '=', self.id)]
        domain_json = json.dumps(domain)
        action_id = self.env.ref('cm_airline_ticket_request.action_ticket_request_cm')
        base_url += '/web#action=%s&model=%s&view_type=list&domain=%s' % (
            action_id.id,
            self._name,
            domain_json
        )
        template_id = self.env.ref('cm_airline_ticket_request.ticket_request_created_template')
        if self.request_type == 'round_trip':
            type_r = 'Ida y Vuelta'
        elif self.request_type == 'exit_only':
            type_r = "Solo Ida"
        else:
            type_r = "Multiple"

        template_ctx = {
            'action_url': base_url,
            'program_code': self.program_id.code,
            'type': type_r,
            'user': self.user_id.name,
            'name': self.name,
        }
        template_id.with_context(**template_ctx).send_mail(
            self.id, 
            force_send=True,
            email_values={
                'email_to': 'conectividad@cmairlines.com',
            }
        )

    def send_finalize_mail(self):
        email_to = ''
        if self.notifications_select == 'applicant':
            email_to = self.user_id.login

        attachment_ids = []
        if self.only_pnr:
            if self.pnr_file:
                attachment = {
                    'name': self.pnr_file_name or 'PNR.pdf',
                    'type': 'binary',
                    'datas': self.pnr_file,
                    'mimetype': 'application/pdf'
                }
                attachment_ids.append((0, 0, attachment))
        else:
            for line in self.list_request_ids:
                if line.pnr_file:
                    attachment = {
                        'name': line.pnr_file_name or 'PNR.pdf',
                        'type': 'binary',
                        'datas': line.pnr_file,
                        'mimetype': 'application/pdf'
                    }
                    attachment_ids.append((0, 0, attachment))

        mail_obj = self.env['mail.mail']
        mail_values = {
            'subject': f'Solicitud Finalizada - {self.name}',
        }
        if self.notifications_select == 'applicant':
            body = self.create_body(self.user_id.name, self.notifications_select)
            mail_values.update(
                {
                'body_html': body,
                'email_to': self.user_id.login,
                'attachment_ids': attachment_ids,
            })
            # Crear y enviar correo
            mail = mail_obj.create(mail_values)

            mail.send()
        else:
            body = self.create_body(self.user_id.name, 'appplicant_passenger')

            mail_values.update(
                {
                'body_html': body,
                'email_to': self.user_id.login
            })
            # Crear y enviar correo
            mail = mail_obj.create(mail_values)
            mail.send()

            for line in self.list_request_ids:
                body = self.create_body(line.name, self.notifications_select)
                mail_values.update({
                    'body_html': body,
                    'email_to': line.email,
                    'attachment_ids': attachment_ids,
                })
                mail = mail_obj.create(mail_values)
                mail.send()

    def create_body(self, name, type_n):
        if type_n == 'applicant':
            message = f"""{name} Se ha finalizado su solicitud de boletos, se adjunta el o los documentos con los pnr asignados."""
        elif type_n == 'passengers':
            message = f"""{name} Se ha finalizado la solicitud de boletos creada por {self.user_id.name}, se adjunta el documento con el pnr asignado."""
        else:
            message = f"""Se ha finalizado su solicitud de boletos creada; fue enviado el documento con el pnr asignado a cada pasajero ingresado."""

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
                                                            <span style="font-size: 10px;">Solicitud Finalizada</span><br/>
                                                            {name}
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
                                                                {message_str}
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
            """.format(name=self.name, message_str=message)
        return body

    def unlink(self):
        if self.state != 'draft':
            raise ValidationError("Solo puede borrar solicitudes en estado borrador")
        return super(ticket_request, self).unlink()	

    def split_request(self):
        split_request_ids = self.list_request_ids.filtered(lambda line: line.split == True)
        if split_request_ids:
            self.ensure_one()
            sequence_id = self.env.ref('cm_airline_ticket_request.sequence_ticket_request_cm')
            new_request_id = self.copy({
                'name': 'Borrador',
                'state': self.state,
                'program_code': self.program_id.code,
                'list_request_ids': [(5, 0, 0)],
                'only_pnr': False,
                'pnr': False,
                'pnr_file': False,
                'pnr_file_name': False
            })
            print (new_request_id.name)
            for req in split_request_ids:
                req.write({'request_id': new_request_id.id})
            next_number = sequence_id.next_by_id()
            new_request_id.write({'name': next_number, 'state': self.state})
        else:
            raise ValidationError("No hay nada que dividir.")


class routes_lines(models.Model):    
    _name = 'cm.routes.line'
    _description = "Lista de rutas"

    request_id = fields.Many2one('cm.ticket.request',string="Solicitud")
    route_id = fields.Many2one('flight.routes', string="Ruta")
    date = fields.Date(string="Fecha")
    flight_select = fields.Selection([('am','AM'),('pm','PM')],string="Vuelo/Horario")
    observations = fields.Text(string="Observaciones")
    sequence = fields.Integer(string="No.", default=1, readonly=True)
    ticket_type = fields.Selection([('one_way','IDA'),('return','VUELTA')],string="Tipo de Viaje")

class ticket_request_line(models.Model):    
    _name = 'cm.ticket.request.line'
    _description = "Lista de boletos"

    request_id = fields.Many2one('cm.ticket.request',string="Solicitud")
    user_id = fields.Many2one('res.users',string="Solicitante")
    name = fields.Char(string="Nombre")
    id_number = fields.Char(string="Id/Pasaporte")
    class_name = fields.Char(string="Clase")
    email = fields.Char(string="Correo Electronico")
    phone = fields.Char(string="Telefono")
    nationality = fields.Char(string="Nacionalidad")
    birthdate = fields.Date(string="Fecha de Nacimiento")
    description = fields.Text(string="Descripcion")
    more_luggage = fields.Boolean(string="Mas Equipaje?")
    employee_id = fields.Many2one('hr.employee',string="Usuario Interno")
    external_user_id = fields.Many2one('cm.ticket.request.external',string="Usuario Externo")
    user_external = fields.Boolean(string="Externo")
    pnr = fields.Char(string="PNR",copy=False)
    state = fields.Selection(related='request_id.state',string="Estado")
    split = fields.Boolean(string="Dividir")
    pnr_file = fields.Binary(string="Doc PNR",copy=False)
    pnr_file_name = fields.Char(string="Nombre PNR",copy=False)
    id_file = fields.Binary(string="Doc ID",copy=False)
    id_file_name = fields.Char(string="Nombre ID",copy=False)
    only_pnr = fields.Boolean(string="Unico PNR",related="request_id.only_pnr")

    @api.onchange('user_external','employee_id','external_user_id')
    def get_data(self):
        if self.user_external:
            user_name = self.external_user_id.name
            identity = self.external_user_id.id_number
            email = self.external_user_id.email
            phone = self.external_user_id.phone
            birthdate = self.external_user_id.birthdate
            nationality = self.external_user_id.nationality
            if self.external_user_id.id_file:
                self.id_file = self.external_user_id.id_file
                self.id_file_name = self.external_user_id.id_file_name
        else:
            user_name = self.employee_id.name
            identity = self.employee_id.identification_id
            email = self.employee_id.work_email or self.employee_id.private_email
            phone = self.employee_id.mobile_phone or self.employee_id.private_phone
            birthdate = self.employee_id.birthday
            nationality = self.employee_id.country_of_birth.name

        self.name = user_name
        self.id_number = identity
        self.email = email
        self.phone = phone
        self.birthdate = birthdate
        self.nationality = nationality


class external_resquest(models.Model):    
    _name = 'cm.ticket.request.external'
    _description = "Personas Externas"

    name = fields.Char(string="Nombre")
    id_number = fields.Char(string="Id/Pasaporte")
    class_name = fields.Char(string="Clase")
    email = fields.Char(string="Correo Electronico")
    phone = fields.Char(string="Telefono")
    nationality = fields.Char(string="Nacionalidad")
    birthdate = fields.Date(string="Fecha de Nacimiento")
    id_file = fields.Binary(string="Doc ID",copy=False)
    id_file_name = fields.Char(string="Nombre ID",copy=False)

    _id_number_unique = models.Constraint('unique(id_number)', message='Ya existe otro registro con el mismo numero de Id/Pasaporte!')

class program_resquest(models.Model):    
    _name = 'cm.ticket.request.program'
    _description = "Programas de solicitudes"

    name = fields.Char(string="Nombre")
    default_program = fields.Boolean(string="Programa por defecto")
    code = fields.Char(string="Codigo")

class airline_resquest(models.Model):    
    _name = 'cm.ticket.request.airline'
    _description = "Aerolinea"

    name = fields.Char(string="Nombre")
    default_airline = fields.Boolean(string="Aerolinea por defecto")
    code = fields.Char(string="Codigo")
    contact_email = fields.Char(string="Correos de contacto")
    country_id = fields.Many2one('res.country',string='Pais')
    ticket_type_request = fields.Selection([('internal','Interno'),('external','Externo')],string="Tipo de solicitud")