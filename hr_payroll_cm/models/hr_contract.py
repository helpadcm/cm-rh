from odoo import fields, models


class Contract(models.Model):
    _inherit = 'hr.contract'

    hours_per_week = fields.Float(
        string='Horas por Semana',
        help='Horas de trabajo por semana',
        tracking=True,
        default=44.0
        )
