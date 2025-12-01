# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError

class businessList(models.Model):    
    _name = 'cm.business.list'
    _description = "Lista de Negocios"

    name = fields.Char(string="Nombre")
    email = fields.Char(string="Correo de contacto")
    business_type = fields.Selection([('hotel','Hotel'),('ferry','Ferry')],string="Tipo de negocio")
    phone = fields.Char(string="Telefono")
    cc_email = fields.Char(string="CC Correos")

class ferryRoutes(models.Model):    
    _name = 'cm.ferry.routes'
    _description = "Rutas de Ferry"

    name = fields.Char(string="Nombre")
    origin = fields.Char(string="Origen")
    destination = fields.Char(string="Destino")

    @api.onchange('origin','destination')
    def create_route_name(self):
        if self.origin and self.destination:
            self.name =  f"""{self.origin} - {self.destination}"""