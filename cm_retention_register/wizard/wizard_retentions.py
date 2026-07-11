# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class wizardRetentions(models.TransientModel):
    _name = "retention.wizard_retentions"
    _description = "Reporte de retenciones"

    date_start = fields.Date(string="Fecha Inicial")
    date_to = fields.Date(string="Fecha Final")
   
    def check_report(self):
        datas = {}
        datas['model'] = 'retentions'
        datas['form'] = self.read(['date_start', 'date_to'])[0]
        used_context = self.env.context
        datas['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'es'))
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
    
        if self.env.context.get('export_excel'):
            return self.env.ref('cm_retention_register.action_retentions_report_xls').report_action(self,data=datas)

        res = self._print_report(datas)
        return res

    def _print_report(self, data, context=None):
        return self.env.ref('cm_retention_register.retentions_retention_report').report_action(self, data=data)

    @api.constrains('date_start','date_to')
    def valid_dates(self):
        if self.date_start and self.date_to:
            if self.date_start > self.date_to:
                raise ValidationError("La fecha inicial no puede ser mayor que la fecha final")
