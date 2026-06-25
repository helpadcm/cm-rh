# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class wizard_check_list(models.TransientModel):
    _name = "report_check.wizard_check_list"
    _description = "Reporte de cheques"

    payment_date_start = fields.Date(string="Fecha de Inicio")
    payment_date_end = fields.Date(string="Fecha Fin")
    partner_id = fields.Many2one('res.partner', string="Empresa")
    journal_id = fields.Many2one('account.journal',string="Diario")
    company_id = fields.Many2one('res.company',string="Compañia")
    state   =   fields.Selection([('anulated','Anulado'),('validated','Validado')],string="Estado")

    def print_check_list(self, data, context=None):
        return self.env.ref('cm_reports.report_check_check_list').report_action(self, data = data)
    
    def check_report(self):
        datas = {}
        datas['model'] = 'account.payment'
        datas['form'] = self.read(['payment_date_start', 'payment_date_end','partner_id','journal_id','company_id','state'])[0]
        used_context = self.env.context
        datas['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'es'))
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        if self.env.context.get('export_excel'):
            return self.export_xls(datas)
        data2={}
        res=self.print_check_list(datas)
        return res


    @api.constrains('date_start','date_to')
    def valid_dates(self):
        if self.date_start and self.date_to:
            if self.date_start > self.date_to:
                raise ValidationError("La fecha inicial no puede ser mayor que la fecha final")

    def export_xls(self,datas):
        context = self.env.context
        return self.env.ref('cm_reports.report_check_check_list_xls').report_action(self,data = datas)