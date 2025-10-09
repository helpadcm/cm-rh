# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from math import ceil,floor
from odoo import api, models, fields,_
from dateutil import parser
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class reporte_retencion(models.AbstractModel):
    _name = 'report.cm_retention_register.ret_report_retention'
    _description = "Reporte general retenciones"

    @api.model
    def _get_report_values(self, docids, data=None):
        docids, vals = self.get_ids(data)
        data, vals1 = self.get_data(docids,vals)
        docargs = {
            'data':data,
            'vals':vals1,
        }
        return docargs

    @api.model
    def render_xls(self,vals):
        docids,vals=self.get_ids(vals.get('form'))
        data,vals1 = self.get_data(docids,vals)
        docargs = {
            'data':data,
            'vals':vals1,
        }
        return docargs

    def get_ids(self,data):
        if data.get('form') == None:
            form = data
        else:
            form = data.get('form')
        domain = [('state','=','close')]
        vals={}
        retentions = self.env['retentions']
        if form.get('date_start'):
            vals.update({'date_start': self.change_format(form.get('date_start'))})
            domain.append(('date','>=',form.get('date_start')))
        if form.get('date_to'):
            vals.update({'date_to':self.change_format(form.get('date_to'))})
            domain.append(('date','<=',form.get('date_to')))
        obj_retentions = retentions.search(domain)
        return obj_retentions.ids,vals

    def get_data(self,ids,vals):
        info_retention = []
        total_base = 0
        total_tax = 0
        ids_retentions = []
        no_replicas = []
        count = len(self.env['retentions'].browse(ids))
        for retention in self.env['retentions'].browse(ids):
            retention_line = {}
            if retention.ref_doc_type == 'invoice':
                doc_type = _('Factura')
            elif retention.ref_doc_type == 'ticket':
                doc_type = _('Boleto')
            elif retention.ref_doc_type == 'receipt':
                doc_type = _('Recibo')
            elif retention.ref_doc_type == 'sales_ticket':
                doc_type = _('Venta de Boleto')
            elif retention.ref_doc_type == 'rent_receipt':
                doc_type = _('Recibo de alquiler')
            elif retention.ref_doc_type == 'fees_receipt':
                doc_type = _('Recibo de honorarios')

            if retention.state == 'close':
                state = _('Cerrao')
            elif retention.state == 'cancel':
                state = _('Cancelado')

            amounts, tax, description, concept = self.get_lines(retention.retention_lines)
            replica_number,higher = self.no_replica(retention.name)
            if replica_number == 1:
                info_retention.append({
                    'type': doc_type or '',
                    'rtn': retention.partner_rtn or '',
                    'names': retention.partner_name or '',
                    'document_number': retention.display_name or '',
                    'document_date': self.change_format(retention.date),
                    'amounts': amounts,
                    'tax': tax,
                    'description': description or '',
                    'concept': concept or '',
                    'state': state,
                    'state2': retention.state,
                    'retention_cai': retention.cai_ret or '',
                    'invoice_date': self.change_format(retention.invoice_id.invoice_date),
                    'invoice_number': retention.invoice_id.ref or '',
                    'invoice_cai': retention.cai_shot or '',
                    'count': count
                })
                total_base+=sum(retention.retention_lines.mapped('base_amount'))
                total_tax+=sum(retention.retention_lines.mapped('amount'))
                vals.update({
                    'company_id': retention.invoice_id.company_id,
                    'company_name': retention.invoice_id.company_id.name,
                    'company_header': retention.invoice_id.company_id.company_motto,
                    'company_rtn': retention.invoice_id.company_id.company_registry,
                    'total_base': total_base,
                    'total_tax': total_tax
                })
            else:
                for retention2 in self.env['retentions'].browse(higher):
                    if retention2.ref_doc_type == 'invoive':
                        doc_type = _('Factura')
                    elif retention2.ref_doc_type == 'ticket':
                        doc_type = _('Boleto')
                    elif retention2.ref_doc_type == 'receipt':
                        doc_type = _('Recibo')
                    elif retention2.ref_doc_type == 'sales_ticket':
                        doc_type = _('Venta de boletos')
                    elif retention2.ref_doc_type == 'rent_receipt':
                        doc_type = _('Recibo de alquiler')
                    elif retention2.ref_doc_type == 'fees_receipt':
                        doc_type = _('Recibo de honorarios')

                    if retention2.state == 'close':
                        state = _('Cerrado')
                    elif retention2.state == 'cancel':
                        state = _('Cancelado')

                    amounts, tax, description, concept = self.get_lines(retention2.retention_lines)
                    if retention2.id not in no_replicas:
                        info_retention.append({
                        'type': doc_type,
                        'rtn': retention2.partner_rtn or '',
                        'names': retention2.partner_name or '',
                        'document_number': retention2.display_name or '',
                        'document_date': self.change_format(retention2.date),
                        'amounts': amounts,
                        'tax': tax,
                        'description': description or '',
                        'concept': concept or '',
                        'state': state,
                        'state2': retention2.state,
                        'retention_cai': retention2.cai_ret or '',
                        'invoice_date': self.change_format(retention2.invoice_id.invoice_date),
                        'invoice_number': retention2.invoice_id.ref or '',
                        'invoice_cai': retention2.cai_shot or '',
                        'count': count
                        })
                        total_base+=sum(retention2.retention_lines.mapped('base_amount'))
                        total_tax+=sum(retention2.retention_lines.mapped('amount'))
                        vals.update({
                            'company_name': retention2.invoice_id.company_id.name,
                            'company_header': retention2.invoice_id.company_id.company_motto,
                            'company_rtn': retention2.invoice_id.company_id.company_registry,
                            'total_base': total_base,
                            'total_tax': total_tax
                        })
                    no_replicas.append(retention2.id)
            count-=1
        total_base1 = 0
        total_base10 = 0
        total_base12 = 0
        total_base25 = 0
        total_amount1 = 0
        total_amount10 = 0
        total_amount12 = 0
        total_amount25 = 0
        for i in info_retention:
            if i.get('state2') == 'close':
                total_base1 += i.get('amounts').get('base_1')
                total_base10 += i.get('amounts').get('base_10')
                total_base12 += i.get('amounts').get('base_12')
                total_base25 += i.get('amounts').get('base_25')
                total_amount1 += i.get('amounts').get('amount_1')
                total_amount10 += i.get('amounts').get('amount_10')
                total_amount12 += i.get('amounts').get('amount_12')
                total_amount25 += i.get('amounts').get('amount_25')
        vals.update({
            'total_base1':total_base1,
            'total_base10':total_base10,
            'total_base12':total_base12,
            'total_base25':total_base25,
            'total_amount1':total_amount1,
            'total_amount10':total_amount10,
            'total_amount12':total_amount12,
            'total_amount25':total_amount25,
        })
        data=[]
        data=sorted(info_retention,key=lambda x:x.get('document_number'))
        return data,vals

    def change_format(self,date):
        if date:
            formato_fecha = "%d/%m/%Y"
            fecha_inicial = datetime.strptime(str(date), "%Y-%m-%d")
            fecha = datetime.strftime(fecha_inicial, formato_fecha)
            return fecha


    def get_lines(self,lines):
        base_1 = 0
        base_10 = 0
        base_12 = 0
        base_25 = 0
        amount_1 = 0
        amount_10 = 0
        amount_12 = 0
        amount_25 = 0
        tax = 0
        description = ''
        concept = ''
        for i in lines:
            base_amount = i.base_amount
            if base_amount == 0:
                base_amount = i.retention_id.invoice_id.amount_untaxed

            if i.account_id.retention_porcent == 1.0:
                base_1 += base_amount
                amount_1 += i.amount
            elif i.account_id.retention_porcent == 10.0:
                base_10 += base_amount
                amount_10 += i.amount
            elif i.account_id.retention_porcent == 12.5:
                base_12 += base_amount
                amount_12 += i.amount
            elif i.account_id.retention_porcent == 25.0:
                base_25 += base_amount
                amount_25 += i.amount
            tax+=i.amount
            if i.account_id.tax_description:
                description += i.account_id.tax_description + ',  '
            if i.account_id.retention_concept:
                concept += i.account_id.retention_concept + ',  '
        
        amounts = {
            'base_1': base_1,
            'base_10': base_10,
            'base_12': base_12,
            'base_25': base_25,
            'amount_1': amount_1,
            'amount_10': amount_10,
            'amount_12': amount_12,
            'amount_25': amount_25
        }
        return amounts,tax, description, concept

    def no_replica(self,name):
        higher = max(self.env['retentions'].search([('name','=',name)]).ids)
        number = len(self.env['retentions'].search([('name','=',name)]))
        return number,higher