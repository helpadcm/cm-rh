# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from math import ceil,floor
from odoo import api, models, fields
from dateutil import parser
from dateutil.relativedelta import relativedelta

class ReportHandling(models.AbstractModel):
    _name = 'report.cm_reports.report_ticket'
    _description = "Boletos"

    @api.model
    def _get_report_values(self, docids, data=None):
        # vals = self.get_data(data)
        data = self.get_data(docids)
        docargs = {
            'info':data.get('info'),
            'invoices':data.get('info_invoice'),
            'sum_gravado':data.get('sum_gravado'),
            'excento':data.get('excento'),
            'suma':data.get('suma_total'),
            'conv_suma_total':data.get('conv_suma_total'),
            'agente':data.get('agent'),
            'origin':data.get('origin'),
            'origins':data.get('origins'),
            'name':data.get('name'),
            'rtn_cliente':data.get('rtn_cliente'),
        }
        return docargs

    def get_data(self,ids):
        account_invoice = self.env.get('account.move').search([('id','in',ids),('state','in',['posted']),'|',('is_sync','=',True),('modality','=',False)])
        info = []
        info_order = []
        info_invoice = []
        origins = []
        for invoice in account_invoice.with_context(lang='es_CR'):
            filtered_lines = invoice.invoice_line_ids.filtered("sub_invoice")
            info_lines = self.get_lines(filtered_lines)
            dic_total = self.get_gravado_total(info_lines)
            dic_exento = self.excento(filtered_lines)

            city_state = invoice.company_id.city 
            if  invoice.company_id.state_id:
                city_state += ", " + invoice.company_id.state_id.name
            rate = invoice.currency_rate
            text_amount = invoice.amount_in_words
            info_invoice.append( {
            'text_amount': text_amount,
            'partner_id': invoice.partner_id,
	        'company_id': invoice.company_id,
            'name': invoice.partner_name or invoice.partner_id.name,
            'street': invoice.partner_id.street,
            'street2': invoice.partner_id.street2,
            'city': invoice.partner_id.city,
            'state': invoice.partner_id.state_id.name,
            'country': invoice.partner_id.country_id.name,
            'identity': invoice.partner_id.ref,
            'phone': invoice.partner_id.phone,
            'email_company': invoice.company_id.email,
            'phone_company': invoice.company_id.phone,
            'fecha_factura' : self.change_format(invoice.invoice_date),
            'number_factura' : invoice.name,
            'date_due' : self.change_format(invoice.invoice_date_due),
            'payment_term' : invoice.invoice_payment_term_id.name,
            'origin' : invoice.origin,
            'cai_shot' : invoice.cai_number or False,
            'expire_cai' : self.change_format(invoice.expiration_cai_date) or False,
            'min_cai' : invoice.min_number_cai or False,
            'max_cai' : invoice.max_number_cai or False,
            'lps_amount': invoice.amount_total_signed,
	        'amount_tax': invoice.amount_tax,
            'base_imponible': invoice.amount_untaxed,
            'rate': rate,
            'name_company': invoice.company_id.name,
            'street_company': invoice.company_id.street,
            'street2_company': invoice.company_id.street2,
            'city_state': city_state,
            'rtn': invoice.company_id.company_registry,
            'modality': invoice.invoice_payment_term_id.name or "",
            'estado': invoice.state,
            'exento': dic_exento.get('excento'),
            'conv_exento': dic_exento.get('conv_excento'),
            'amount_total': invoice.amount_total,
            'origen': invoice.ref,
            'rtn_cliente': invoice.rtn_name or invoice.partner_id.vat,
            'agente': invoice.invoice_user_id.name or '',
            'subtotal': invoice.amount_untaxed - float(dic_total.get('suma_otros'))- 0,
            'discount': 0,
            'pnr': invoice.pnrcode,
            'lines': info_lines,
            'gravado_total': dic_total.get('suma_gravado'),
            'suma_otros': dic_total.get('suma_otros'),
            'name_currency': invoice.currency_id.name,
	        'company_currency': invoice.company_id.currency_id.name,
            'exempt_purchase': invoice.purchase_order_exempt,
            'exonerated_record': invoice.record_exonerated,
            'reg_sag': invoice.sag_record
            })
        return {'info_invoice':info_invoice,'info':info}

    def get_lines(self,lines):
        invoice_data = []
        for i in lines:
            exento=0
            donate=0
            gravado=0.0
            if i.donate:
                donate= i.price_unit
            elif not (i.tax_ids):
                exento = i.price_unit+i.YQAmount
            else:
                gravado=  i.price_unit
            invoice_data.append({
                        'gravado':self.set_precision(gravado),
                        'exento':self.set_precision(exento),
                        'donate':self.set_precision(donate),
                        'description': i.name or '',
                        'yq':i.YQAmount,
                        'rate':i.TAAmount + i.TIAmount + i.TDAmount,
                        'yryz':i.YRAmount + i.YZAmount,
                        'ta':i.TAAmount,
                        'td':i.TDAmount,
                        'ti':i.TIAmount,
                        'yr':i.YRAmount,
                        'yz':i.YZAmount,
                        'quantity':int(i.quantity)
                        }
                        )              
        return invoice_data
        
    def excento(self,lines):
        excento = 0.00
        for line in lines:
            if line.donate:
                continue
            if not line.tax_ids:
                excento += line.price_unit+line.YQAmount+line.YRAmount+line.YZAmount
        return {'excento':self.set_precision(excento),'conv_excento':self.set_precision(excento)}

    def change_format(self,date):
        if date:
            formato_fecha = "%d/%m/%Y"
            fecha = datetime.strftime(date,formato_fecha)
            return fecha

    def get_gravado_total(self,info):
        suma_gravado = 0.00
        suma_donate = 0.00
        suma_yq = 0.00
        suma_ta = 0.00
        suma_yr = 0.00
        suma_td = 0.00
        suma_ti = 0.00
        suma_yz = 0.00
        for i in info:
            if i.get('exento') =='0.00':
                suma_gravado += (float(i.get('gravado')))+float(i.get('yryz'))
                suma_yq += float(i.get('yq'))
            suma_ta += float(i.get('ta'))
            suma_yr += float(i.get('yr'))
            suma_td += float(i.get('td'))
            suma_ti += float(i.get('ti'))
            suma_yz += float(i.get('yz'))
            suma_donate += float(i.get('donate'))
        suma_total_otros = suma_ta+suma_donate+suma_td+suma_ti
        suma_total_gravado = suma_gravado + suma_yq
        return {'suma_gravado':suma_total_gravado,'suma_otros':suma_total_otros}


    def set_precision(self,num):
        return "{0:.2f}".format(num)

    def set_precision2(self,num):
        return "{0:.4f}".format(num)
