# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

opt_reports = [
    ('1','Volumenes totales'),
    ('2','Guias abandonadas'),
    ('3','Revision de Guias'),
    ('4','Descuentos aplicados'),
    ('5','Ventas Diarias'),
]

class handlingReport(models.TransientModel):
    _name = "handling.reports"
    _description = "Reportes de encomiendas"

    initial_date = fields.Date(string="Fecha Inicial")
    final_date = fields.Date(string="Fecha Final")
    partner_ids = fields.Many2many('res.partner',string="Clientes")
    detail = fields.Boolean(string="Detallar")
    report_opt = fields.Selection(opt_reports, string="Reporte")
    origin_id = fields.Many2one('cargo.station', string="Origen")
    destination_id = fields.Many2one('cargo.station', string="Destino")

    def print_report(self):
        data = {
            'initial_date': self.initial_date,
            'final_date': self.final_date,
            'detail': self.detail,
            'partner_ids': self.partner_ids.ids,
            'origin_id': self.origin_id.id or False,
            'destination_id': self.destination_id.id or False,
            'origin_name': self.origin_id.ref or False,
            'destination_name': self.destination_id.ref or False,
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
        elif self.report_opt == '5':
            print_excel = self.env.context.get('print_excel')
            if print_excel:
                return self.env.ref('cm_cargo_handling.action_daily_sales_report_xlsx').report_action(self,data=data)
            else:
                return self.env.ref('cm_cargo_handling.action_daily_sales_report').report_action(self,data=data)
        else:
            return True

    @api.constrains('origin_id', 'destination_id')
    def validate_point_of_sale(self):
        if self.origin_id and self.destination_id:
            if self.origin_id.id == self.destination_id.id:
                raise ValidationError("El origen y el destino no pueden ser iguales")