from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AffCostTemplate(models.Model):
    _name = 'aff.cost.template'
    _description = 'Plantilla de Costeo Dinámica'

    name = fields.Char(string='Nombre de la Plantilla', required=True)
    variable_ids = fields.One2many(
        'aff.cost.template.variable', 
        'template_id', 
        string='Campos / Variables Requeridas'
    )
    formule = fields.Char(
        string='Fórmula de Cálculo', 
        help="Escribe la fórmula matemática usando los códigos de las variables. Ej: (precio * cantidad)"
    )

class AffCostTemplateVariable(models.Model):
    _name = 'aff.cost.template.variable'
    _description = 'Variable de la Plantilla'
    _order = 'sequence, id'

    template_id = fields.Many2one('aff.cost.template', ondelete='cascade')
    sequence = fields.Integer(string='Secuencia', default=10)
    name = fields.Char(string='Nombre del Campo', required=True)
    field_type = fields.Selection([
        ('float', 'Número Decimal'),
        ('monetary', 'Monto Monetario'),
        ('integer', 'Número Entero')
    ], string='Tipo de Dato', default='float', required=True)
    code = fields.Char(
        string='Código (Para Fórmula)', 
        required=True, 
        help="Código único en minúsculas y sin espacios. Ej: precio_galon"
    )

    _code_unique = models.Constraint('unique(template_id,code)', message='El código de la variable ya existe en esta plantilla.')
    
class AffFixedCostValue(models.Model):
    _name = 'aff.fixed.cost.value'
    _description = 'Valores de Variables para Costo Fijo'

    fixed_line_id = fields.Many2one('fixed.cost.lines', ondelete='cascade')
    variable_id = fields.Many2one('aff.cost.template.variable', string='Parámetro', readonly=True)
    field_type = fields.Selection(related='variable_id.field_type', readonly=True)
    value_float = fields.Float(string='Valor (Decimal)')
    value_integer = fields.Integer(string='Valor (Entero)')


class AffVariableCostValue(models.Model):
    _name = 'aff.variable.cost.value'
    _description = 'Valores de Variables para Costo Variable'

    variable_line_id = fields.Many2one('variable.cost.lines', ondelete='cascade')
    variable_id = fields.Many2one('aff.cost.template.variable', string='Parámetro', readonly=True)
    field_type = fields.Selection(related='variable_id.field_type', readonly=True)
    value_float = fields.Float(string='Valor (Decimal)')
    value_integer = fields.Integer(string='Valor (Entero)')