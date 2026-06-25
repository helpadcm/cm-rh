# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from math import ceil,floor
from odoo import api, models, fields,_
from dateutil import parser
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class ReportCheckList(models.AbstractModel):
    _name = 'report.cm_reports.report_check_list'
    _description = "Listado de cheques"

    @api.model
    def _get_report_values(self, docids, data=None):
        # vals = self.get_data(data)
        data = self.get_data(data.get('context',{}).get('active_ids',[]))
        docargs = {
            'info_report':data.get('data'),
            'info_wizard':data.get('info_wizard')
        }
        return docargs
	
    @api.model
    def render_xls(self, docids, data=None):
        res = {}
        data = self.get_data(docids.ids)
        docargs = {
            'info_report':data.get('data'),
            'info_wizard':data.get('info_wizard')
        }
        return docargs

    def get_data(self,ids):
        info_wizard = self.env['report_check.wizard_check_list'].browse(ids)
        account_payment = self.env['account.payment']
        mcheck_mcheck = self.env['mcheck.mcheck']
        mcheck_name = self.env['mcheck.mcheck_name']
        payment_line = self.env['account.payment.line']
        domain_payment = [('pay_method_type','=','check')]
        domain_check = [('doc_type','=','check')]
        info_report=[]
        for info in info_wizard:
            if not info.state:
                domain_check.append(('state','in',['validated','anulated']))
                domain_payment.append(('state','in',['in_process','paid','rejected','canceled']))
            else:
                if info.state == 'validated':
                    domain_payment.append(('state','in',['in_process','paid']))
                else:
                    domain_payment.append(('state','in',['rejected','canceled']))    
                domain_check.append(('state','=',info.state))
            if info.payment_date_start:
                domain_payment.append(('date','>=',info.payment_date_start))
                domain_check.append(('date','>=',info.payment_date_start))
            if info.payment_date_end:
                domain_payment.append(('date','<=',info.payment_date_end))
                domain_check.append(('date','<=',info.payment_date_end))
            if info.partner_id:
                domain_payment.append(('partner_id','=',info.partner_id.id))
                domain_check.append(('doc_type','!=','check'))
            if info.journal_id:
                domain_payment.append(('journal_id','=',info.journal_id.id))
                domain_check.append(('journal_id','=',info.journal_id.id))
            if info.company_id:
                domain_payment.append(('company_id','=',info.company_id.id))            

        obj_payment = account_payment.search(domain_payment)
        obj_mcheck = mcheck_mcheck.search(domain_check)
        
        if len(obj_payment)>0:
            for i in obj_payment:
                if i.partner_type == 'supplier':
                    if i.state == 'in_process' or i.state == 'paid':
                        state = _('Validado')
                    elif i.state == 'canceled' or i.state == 'rejected':
                        state = _('Anulado')
                    info_report.append({
                        'affair':i.communication or '',
                        'beneficiary':i.partner_id_for_parents.name,
                        'date':self.change_format(i.date),
                        'state':state,
                        'bank_account':i.journal_id.bank_account_id.acc_number,
                        'number':i.name,
                        'amount':i.amount,
                        'currency':i.currency_id.symbol or '',
                        'journal':i.journal_id.name

                    })
        if len(obj_mcheck)>0:
            for i in obj_mcheck:
                if i.state == 'validated':
                    state = _('Validado')
                elif i.state == 'anulated':
                    state = _('Anulado')
                info_report.append({
                    'affair':i.name or '',
                    'beneficiary':i.reference,
                    'date':self.change_format(i.date),
                    'state':state,
                    'bank_account':i.journal_id.bank_account_id.acc_number,
                    'number':i.number,
                    'amount':i.total,
                    'currency':i.journal_id.currency_id.symbol or '',
                    'journal':i.journal_id.name
                })
        #info_report.sort(key=lambda x:x.get('number'))
        data=[]
        data=sorted(info_report,key=lambda x:x.get('number'))
        return {'data':data, 'info_wizard':info_wizard}

    def change_format(self,date):
        if date:
            formato_fecha = "%d/%m/%Y"
            # fecha_inicial = datetime.strptime(date, "%Y-%m-%d")
            fecha = datetime.strftime(date,formato_fecha)
            return fecha