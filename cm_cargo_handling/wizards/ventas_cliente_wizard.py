from odoo import models, fields

class VentasClienteWizard(models.TransientModel):
    _name = 'ventas.cliente.wizard'
    _description = 'Reporte Ventas por Cliente'

    date_start = fields.Date(string='Fecha Inicial', required=True)
    date_end = fields.Date(string='Fecha Final', required=True)

    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string="Cliente(s)",
        help="Seleccione uno o varios clientes. Si se deja vacío, se generará para todos."
    )

    modality = fields.Selection([
        ('all', 'Todas'),
        ('counted', 'Contado'),
        ('credit', 'Crédito'),
        ('upon_delivery', 'Por Cobrar'),
    ], string='Modalidad', default='all', required=True)

    def action_print_report(self):
        self.ensure_one()
        start_str = self.date_start.strftime('%d-%m-%Y') if self.date_start else ''
        end_str = self.date_end.strftime('%d-%m-%Y') if self.date_end else ''
        filename = f"Ventas por Clientes {start_str} al {end_str}"

        return self.env.ref('cm_cargo_handling.action_ventas_cliente_report_xlsx').with_context(
            report_file_name=filename
        ).report_action(self)
