from odoo import fields, models


class ContractBonusTrasport(models.Model):
    _inherit = 'hr.contract'

    early_checkin_bonus_time = fields.Float(
        string='Hora de Bono de Entrada',
        help='Hora de Bono de Trasporte de Entrada Temprana'
    )
    late_checkout_bonus_time = fields.Float(
        string='Hora de Bono de Salida Tarde',
        help='Hora de Bono de Trasporte de Salida Tarde'
    )
    max_extra_hours = fields.Float(
        string='Máximo de Horas Extras',
        help='Maximo de horas extras que el empleado puede realizar'
    )
    maximus_performance_bonus = fields.Monetary(
        string='Máximo de Bono de Desempeño',
        help='Bono de Desempeño que se le otorgara al empleado'
    )

    transportation_bonus = fields.Integer(
        string='Bono de Trasporte Maximo',
        help='Bono de Trasporte Maximo'
    )
    value_bonus = fields.Monetary(
        string='Valor de Bono',
        help='Valor unitario del bono de transporte'
    )
