# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError

class expensesTicketRequest(models.Model):
    _name = 'cm.expenses.request.ticket'
    _description = "Solicitud de boletos en viaticos"

    @api.model
    def default_get(self, fields):
        rec = super(expensesTicketRequest, self).default_get(fields)
        airline_default_id = self.env['cm.ticket.request.airline'].search([('default_airline','=',True)])
        if airline_default_id:
            rec.update({
                'airline_id': airline_default_id[0].id
            })
        return rec

    name = fields.Char(string="Numero",related="request_ticket_id.name")
    airline_id = fields.Many2one('cm.ticket.request.airline',string="Aerolinea")
    request_type = fields.Selection([('round_trip','Ida y Vuelta'),('exit_only','Solo Ida'),('multiple','Multiple')],string="Tipo de Solicitud", default="round_trip")
    request_ticket_id = fields.Many2one('cm.ticket.request',string="Solicitud de ticket")
    list_routes_ids = fields.One2many('cm.routes.line','expense_line_request_id',string="Listado Rutas")
    expense_request_id = fields.Many2one('cm.expenses.request',string="Solicitud de viaticos")
    more_luggage = fields.Boolean(string="Mas Equipaje?")
    passport_file = fields.Binary(string="ID/Pasaporte")
    passport_file_name = fields.Char(string="Nombre pasaporte")
    ticket_type_request = fields.Selection(string="Tipo de solicitud de boleto",related="airline_id.ticket_type_request")

    quote_file = fields.Binary(string="Cotizacion")
    quote_file_name = fields.Char(string="Nombre Cotización")
    quote_amount = fields.Float(string="Monto de cotización")

class ticket_requestInh(models.Model):    
    _inherit = 'cm.ticket.request'

    expense_request_id = fields.Many2one('cm.expenses.request',string="Solicitud de viaticos")

class routesInh(models.Model):    
    _inherit = 'cm.routes.line'

    expense_line_request_id = fields.Many2one('cm.expenses.request.ticket',string="Solicitud de tickets viaticos")