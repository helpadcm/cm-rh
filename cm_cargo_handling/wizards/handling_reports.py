# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

opt_reports = [
    ('1','Volumenes totales'),
    ('2','Guias abandonadas'),
    ('3','Revision de Guias'),
    ('4','Descuentos aplicados'),
]

class handlingReport(models.TransientModel):
    _name = "handling.reports"
    _description = "Reportes de encomiendas"

    initial_date = fields.Date(string="Fecha Inicial")
    final_date = fields.Date(string="Fecha Final")
    partner_ids = fields.Many2many('res.partner',string="Clientes")
    detail = fields.Boolean(string="Detallar")
    report_opt = fields.Selection(opt_reports, string="Reporte")

    def print_report(self):
        data = {
            'initial_date': self.initial_date,
            'final_date': self.final_date,
            'detail': self.detail,
            'partner_ids': self.partner_ids.ids,
            'report_opt': self.report_opt
        }
        if self.report_opt == '1':
            return self.env.ref('cm_cargo_handling.cargo_volume_handling_xlsx').report_action(self,data=data)
        elif self.report_opt == '2':
            return self.env.ref('cm_cargo_handling.abandoned_guide_report_id').report_action(self,data=data)
        elif self.report_opt == '3':
            return self.env.ref('cm_cargo_handling.cargo_guide_reviews_xlsx').report_action(self,data=data)
        elif self.report_opt == '4':
            return self.env.ref('cm_cargo_handling.action_discount_applied_xlsx').report_action(self,data=data)
        else:
            return True