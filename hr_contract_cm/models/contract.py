from odoo import fields, models


class Contract(models.Model):
    _inherit = 'hr.contract'

    early_checkin_bonus_time = fields.Float(
        string='Hora de Bono de Entrada',
        help='Hora de Bono de Trasporte de Entrada Temprana',
        tracking=True
    )
    late_checkout_bonus_time = fields.Float(
        string='Hora de Bono de Salida Tarde',
        help='Hora de Bono de Trasporte de Salida Tarde',
        tracking=True
    )
    max_extra_hours = fields.Float(
        string='Máximo de Horas Extras',
        help='Máximo de horas extras que el empleado puede realizar',
        tracking=True
    )
    maximus_performance_bonus = fields.Monetary(
        string='Máximo de Bono de Desempeño',
        help='Bono de Desempeño que se le otorgara al empleado',
        tracking=True
    )

    transportation_bonus = fields.Integer(
        string='Bono de Trasporte Máximo',
        help='Bono de Trasporte Máximo',
        tracking=True
    )
    value_bonus = fields.Monetary(
        string='Valor de Bono',
        help='Valor unitario del bono de transporte',
        tracking=True
    )
