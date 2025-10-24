# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from math import ceil,floor
from odoo import api, models, fields, _
from dateutil import parser
from dateutil.relativedelta import relativedelta

class ReportAccountStatus(models.AbstractModel):
    _name = 'report.cm_reports.report_account_status'
    _description = "Estado de cuenta"

    @api.model
    def _get_report_values(self, docids, data=None):
        data, reports_vals = self.get_data(data)
        docargs = {
            'data': data,
            'vals': reports_vals
        }
        return docargs

    @api.model
    def render_xls(self, docids, data=None):
        data, reports_vals = self.get_data(data)
        docargs = {
            'data': data,
            'vals': reports_vals
        }
        return docargs

    def get_data(self,data):
        date_start = data.get('date_start')
        date_to = data.get('date_to')
        partner_ids = data.get('partner_ids')
        zero_balance = data.get('zero_balance')
        payment_state = data.get('payment_state')

        vals = {}
        groups_partner = False
        data_status = []
        data_move = []
        move_data = {}
        array_partner_id = []
        array_partner_id_move = []
        array_accounts = []
        account_id = []
        obj_move = []
        domain_invoice = [('state','=','posted'),('move_type','=','out_invoice')]
        if payment_state == 'pending':
            domain_invoice.append(('payment_state','in',['not_paid','partial']))
        else:
            domain_invoice.append(('payment_state','in',['paid']))

        if date_start:
            vals.update({'date_start': date_start})
            domain_invoice.append(('invoice_date','>=',date_start))
        
        if date_to:
            vals.update({'date_to': date_to})
            domain_invoice.append(('invoice_date','<=',date_to))
        
        if partner_ids:
            domain_invoice.append(('partner_id','in',partner_ids))

        account_move = self.env.get('account.move')
        obj_move = account_move.search(domain_invoice)

        if zero_balance:
            vals.update({'zero': zero_balance})
        # vals.update({'detail': 'Detalles'})
        # vals.update({'configuration_balance':i.configuration.find_balance})
        for inv in obj_move:
            payed_amount = 0
            balance_amount = 0
            if inv.payment_state in ['paid','partial']:
                payed_amount = sum(inv._get_reconciled_payments().mapped('total_usd'))
                if inv.payment_state == 'partial':
                    balance_amount = inv.amount_residual
            elif inv.payment_state in ['not_paid']:
                balance_amount = inv.amount_residual


            vals = {
                'date': inv.invoice_date.strftime('%d/%m/%Y'),
                'pnr': inv.pnrcode,
                'concept': inv.internal_number or inv.name,
                'invoiced_amount': inv.amount_total,
                'paid_amount': payed_amount,
                'company_id':inv.company_id,
                'balance': balance_amount
            }
            if inv.partner_id.id in array_partner_id:
                array_partner_id_move[array_partner_id.index(inv.partner_id.id)]['datas'].append(vals)
                array_partner_id_move[array_partner_id.index(inv.partner_id.id)]['total_invoiced'] += inv.amount_total
                array_partner_id_move[array_partner_id.index(inv.partner_id.id)]['total_payed'] += payed_amount
                array_partner_id_move[array_partner_id.index(inv.partner_id.id)]['total_balance'] += balance_amount
            else:
                array_partner_id.append(inv.partner_id.id)
                array_partner_id_move.append({
                    'partner': inv.partner_id,
                    'total_invoiced': inv.amount_total,
                    'total_payed': payed_amount,
                    'total_balance': balance_amount,
                    'currency_id': inv.currency_id,
                    'symbol': inv.currency_id.symbol,
                    'company_id': inv.company_id,
                    'datas': [vals]
                })
        start_date = datetime.strptime(date_start, '%Y-%m-%d')
        end_date = datetime.strptime(date_to, '%Y-%m-%d')
        ultimate_day = start_date + relativedelta(months=1, day=1 ,days=-1)
        report_vals = {
            'date_from': start_date.strftime('%d/%m/%Y'),
            'fortnight': end_date.strftime('%Y-%m'),
            'maximum_payment': ultimate_day.strftime('%d/%m/%Y'),
            'date_to': end_date.strftime('%d/%m/%Y')
        }
        return array_partner_id_move, report_vals