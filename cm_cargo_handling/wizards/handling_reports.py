# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

opt_reports = [
    ('1','Volumenes totales'),
    ('2','Guias abandonadas')
]

class handlingReport(models.TransientModel):
    _name = "handling.reports"
    _description = "Reportes de encomiendas"

    initial_date = fields.Date(string="Fecha Inicial")
    final_date = fields.Date(string="Fecha Final")
    report_opt = fields.Selection(opt_reports, string="Reporte")

    def print_report(self):
        data = {
            'initial_date': self.initial_date,
            'final_date': self.final_date,
            'report_opt': self.report_opt
        }
        if self.report_opt == '1':
            return self.env.ref('cm_cargo_handling.cargo_volume_handling_xlsx').report_action(self,data=data)
        elif self.report_opt == '2':
            return self.env.ref('cm_cargo_handling.abandoned_guide_report_id').report_action(self,data=data)
        else:
            return True