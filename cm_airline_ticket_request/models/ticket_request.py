# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime

class ticket_request(models.Model):    
    _name = 'cm.ticket.request'
    _description = "Solicitud de boletos"
    _inherit = ['mail.thread','mail.activity.mixin']

    @api.model
    def _get_default_date(self):
        return datetime.now().date()

    @api.model
    def user_default(self):
        return self.env.user.id

    name = fields.Char(string="Numero", default="Borrador", tracking=True)
    user_id = fields.Many2one('res.users',string="Solicitante",default=user_default)
    date = fields.Date(string="Fecha de Creacion", default=_get_default_date)
    request_date = fields.Date(string="Fecha de Solicitud", tracking=True)
    exit_only = fields.Boolean(string="Solo Salida", tracking=True)
    exit_route_id = fields.Many2one('flight.routes', string="Ruta de Salida", tracking=True)
    return_route_id = fields.Many2one('flight.routes', string="Ruta de Regreso", tracking=True)
    state = fields.Selection([('draft','Borrador'),('validated','Validado'),('canceled','Cancelado')], string="Estado", default='draft', tracking=True)
    list_request_ids = fields.One2many('cm.ticket.request.line','request_id',string="Listado")

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

    @api.onchange('user_external','employee_id','external_user_id')
    def get_data(self):
        if self.user_external:
            user_name = self.external_user_id.name
            identity = self.external_user_id.id_number
            email = self.external_user_id.email
            phone = self.external_user_id.phone
            birthdate = self.external_user_id.birthdate
            nationality = self.external_user_id.nationality
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