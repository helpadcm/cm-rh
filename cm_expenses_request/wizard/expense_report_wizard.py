# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

class ExpenseReportWizard(models.TransientModel):
    _name = 'cm.expense.report.wizard'
    _description = 'Asistente de Reporte de Viáticos'

    date_from = fields.Date(string='Fecha de Inicio', required=True)
    date_to = fields.Date(string='Fecha Final', required=True)
    department_ids = fields.Many2many(
        'hr.department', 
        string='Departamentos', 
        help='Seleccione uno o varios departamentos. Si se deja vacío, se incluirán todos.'
    )
    state = fields.Selection([
        ('approved', 'Aprobado'),
        ('assigned', 'Otorgado'),
        ('pending', 'Liquidacion Conforme'),
        ('finalized', 'Finalizado')
    ], string='Estado', help='Seleccione un estado. Si se deja vacío, se incluirán todos los estados.')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to and record.date_from > record.date_to:
                raise ValidationError(_("La fecha final no puede ser menor que la inicial."))

    def action_print_excel(self):
        self.ensure_one()
        # Validación directa de seguridad al presionar el botón
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_("La fecha final no puede ser menor que la inicial."))
            
        return self.env.ref('cm_expenses_request.action_report_expense_xlsx').report_action(self)

    def get_report_filename(self):
        self.ensure_one()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"Reporte_Viaticos_{self.date_from}_al_{self.date_to}_{timestamp}.xlsx"
