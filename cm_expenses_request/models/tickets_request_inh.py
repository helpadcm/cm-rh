# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError

class expensesTicketRequest(models.Model):
    _name = 'cm.expenses.request.ticket'
    _description = "Solicitud de boletos en viaticos"

    @api.model
    def default_get(self, fields):
        user = self.env.user
        employee_id = self.env['hr.employee'].sudo().search([('user_id','=',user.id)])
        rec = super(expensesTicketRequest, self).default_get(fields)
        airline_default_id = self.env['cm.ticket.request.airline'].search([('default_airline','=',True)])
        if airline_default_id:
            rec.update({
                'airline_id': airline_default_id[0].id
            })
        
        if employee_id and employee_id.id_card:
            attachment_id = employee_id.id_card
            attachment_name = f'ID {employee_id.name}'
            rec.update({
                'passport_file': attachment_id,
                'passport_file_name': attachment_name
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
    currency_id = fields.Many2one('res.currency',string="Moneda")

    quote_file = fields.Binary(string="Cotizacion")
    quote_file_name = fields.Char(string="Nombre Cotización")
    quote_amount = fields.Float(string="Monto de cotización")

    @api.constrains('list_routes_ids', 'request_type')
    def validate_routes(self):
        for rec in self:
            if rec.list_routes_ids:
                if len(rec.list_routes_ids) == 0:
                    raise ValidationError("No hay rutas ingresadas a la solicitud")

                if rec.request_type == 'round_trip':
                    if len(rec.list_routes_ids) != 2:
                        raise ValidationError("Si el tipo de solicitud es de Ida y Vuelta debe agregar dos rutas")
                    
                    line1_id = rec.list_routes_ids[0].route_id
                    line2_id = rec.list_routes_ids[1].route_id
                    if line1_id.destination != line2_id.origin:
                        raise ValidationError(f"Si su solicitud es de Ida y Vuelta el destino de su primera ruta ({line1_id.destination}) debe coincidir con el origen de la segunda ({line2_id.origin})")

                    if line2_id.destination != line1_id.origin:
                        raise ValidationError(f"Si su solicitud es de Ida y Vuelta el destino de su segunda ruta ({line2_id.destination}) debe coincidir con el origen de la primera ({line1_id.origin})")

                elif rec.request_type == 'exit_only':
                    if len(rec.list_routes_ids) != 1:
                        raise ValidationError("Si el tipo de solicitud es Solo de Ida debe agregar una ruta")

class ticket_requestInh(models.Model):    
    _inherit = 'cm.ticket.request'

    expense_request_id = fields.Many2one('cm.expenses.request',string="Solicitud de viaticos")

class routesInh(models.Model):    
    _inherit = 'cm.routes.line'

    expense_line_request_id = fields.Many2one('cm.expenses.request.ticket',string="Solicitud de tickets viaticos")

class routesInh(models.Model):    
    _inherit = 'flight.routes'

    exit_tax = fields.Float(string="Impuestos de salida")
    analytic_account_id = fields.Many2one('account.analytic.account',string="Cuenta Analitica")