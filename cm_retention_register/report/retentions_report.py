# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from math import ceil,floor
from odoo import api, models, fields,_
from dateutil import parser
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class reportRetentions(models.AbstractModel):
    _name = 'report.cm_retention_register.report_retention'

    @api.model
    def _get_report_values(self, docids, data=None):
        res = {}
        docids = self.get_ids(data.get('form',{}))
        data, vals = self.get_data(docids)
        docargs = {
            'data':data,
            'vals':vals
        }
        return docargs

    @api.model
    def render_xls(self, docids, data=None):
        res = {}
        if data.get('report_type')== u'xlsx':
            docids=docids.ids
        else:
            docids=None
            
        if not docids:
            docids =self.get_ids(data.get('form',{}))
        data,vals = self.get_data(docids)
        docargs = {
            'data':data,
        }
        return docargs,vals

    def get_ids(self,data):
        form = data
        domain = []
        vals={}
        retentions = self.env.get('retentions')
        if form.get('date_start'):
            vals.update({'date_start':form.get('date_start')})
            domain.append(('date','>=',form.get('date_start')))
        if form.get('date_to'):
            vals.update({'date_to':form.get('date_to')})
            domain.append(('date','<=',form.get('date_to')))
        obj_retentions = retentions.search(domain)
        return obj_retentions.ids

    def get_data(self,ids):
        info_retention = []
        vals ={}
        total_base = 0
        total_tax = 0
        for retention in self.env.get('retentions').browse(ids):
            if retention.ref_doc_type == 'invoice':
                doc_type = _('Factura')
            elif retention.ref_doc_type == 'ticket':
                doc_type = _('Boleto')
            elif retention.ref_doc_type == 'receipt':
                doc_type = _('Recibo')
            elif retention.ref_doc_type == 'sales_ticket':
                doc_type = _('Venta de Boletos')
            elif retention.ref_doc_type == 'rent_receipt':
                doc_type = _('Recibo de alquiler')
            elif retention.ref_doc_type == 'fees_receipt':
                doc_type = _('Recibo de honorarios')

            for line in retention.retention_lines:
                if retention.state == 'close':
                    info_retention.append({
                        'type': doc_type,
                        'rtn': retention.partner_rtn or '',
                        'names': retention.partner_name,
                        'document_number': retention.display_name,
                        'document_date': self.change_format(retention.date),
                        'base': line.base_amount,
                        'tax': line.amount,
                        'description': line.account_id.tax_description or '',
                        'concept': line.account_id.retention_concept or '',
                    })
                    total_base+=line.base_amount
                    total_tax+=line.amount
                else:
                    info_retention.append({
                        'type': doc_type,
                        'rtn': retention.partner_rtn or '',
                        'names': retention.partner_name,
                        'document_number': retention.display_name,
                        'document_date': self.change_format(retention.date),
                        'base': 0,
                        'tax': 0,
                        'description': _('ANULADO'),
                        'concept': line.account_id.retention_concept or '',
                    })
                    total_base+=0
                    total_tax+=0

            vals.update({
                'company_name': retention.invoice_id.company_id.name,
                'company_header': retention.invoice_id.company_id.company_motto,
                'total_base': total_base,
                'total_tax': total_tax
            })
        return info_retention, vals
    
    def get_datas(self,retention_lines):
        amount = 0
        tax = 0
        description = ''
        concept = ''
        for lines in retention_lines:
            amount+=lines.base_amount
            tax+=lines.amount
            description+=lines.account_id.tax_description or '' + ' '
            concept+=lines.account_id.retention_concept or '' + ' '
        return {'amount':amount,'tax':tax, 'description':description, 'concept':concept}

    def change_format(self,date):
        if date:
            formato_fecha = "%d/%m/%Y"
            fecha = datetime.strftime(date, formato_fecha)
            return fecha
