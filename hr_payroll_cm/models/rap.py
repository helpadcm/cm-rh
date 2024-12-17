from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class calculateRAP(models.Model):
    _name = 'hr.settings.rap'
    _description = 'RAP: Configuracion para calculo de RAP'

    name = fields.Char(string="Nombre",default="RAP")
    min_salary = fields.Float(string="Salario minimo")
    percentage = fields.Float(string="Porcentaje")

    @api.model_create_multi
    def create(self, vals_list):
        rap_id = self.env['hr.settings.rap'].search([])
        if len(rap_id) == 1:
            raise ValidationError("Ya existe un registro de configuracion de RAP")
        return super().create(vals_list)