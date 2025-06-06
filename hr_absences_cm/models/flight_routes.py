from odoo import fields, models, api

class flightRoutes(models.Model):
    _name = 'flight.routes'
    _description = "Rutas de vuelo"

    name = fields.Char(string="Nombre")
    origin = fields.Char(string="Origen")
    destination = fields.Char(string="Destino")

    @api.onchange('origin','destination')
    def get_name(self):
        if self.origin and self.destination:
            self.name = f"{self.origin} - {self.destination}"

class paidLeave(models.Model):
    _name = 'paid.leave'
    _description = "Permisos Goce de Sueldo"

    name = fields.Char(string="Nombre")
    concept = fields.Char(string="Concepto")