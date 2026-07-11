from odoo import api, fields, models, _

class calculateRAP(models.Model):
    _name = 'hr.inc.ded.rules'
    _description = 'Resumen de reglas salariales'

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Codigo")
    category_id = fields.Many2one('hr.salary.rule.category', string="Categoria")

    _code_unique = models.Constraint('unique(code)', message='El codigo de la regla debe ser unico')