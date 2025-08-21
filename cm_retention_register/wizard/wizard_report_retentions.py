# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class wizardReportRetentions(models.TransientModel):
    _name = "retention.wizard_report_retentions"
    _description = "Wizard de retenciones"

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
            return self.env.ref('cm_retention_register.action_ret_retentions_report_xls').report_action(self,data=datas)
            
        res=self._print_report(datas)
        return res

    def _print_report(self, data, context=None):
        return self.env.ref('cm_retention_register.ret_retention_report').report_action(self, data = data)

    @api.constrains('date_start','date_to')
    def valid_dates(self):
        if self.date_start and self.date_to:
            if self.date_start > self.date_to:
                raise ValidationError("La fecha inicial no puede ser mayor que la fecha final")

    def export_xls_retentions(self,datas):
        context = self._context
        return {'type': 'ir.actions.report.xml',
                'report_name': 'retentions.report_retention_xls.xlsx',
                'datas': datas,
                'name': _('Retentions Report XLS')
                }