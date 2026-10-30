# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from math import ceil,floor
from odoo import api, models, fields, _
from dateutil import parser
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError,ValidationError

months=["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

class ReportChecks(models.AbstractModel):
    _name = 'report.cm_banks.check_template'
    _description = "Formato de cheque miscelaneo"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = self.get_data(docids)
        mcheck_ids = self.env['mcheck.mcheck'].search([('id','in',docids)])
        docs = mcheck_ids
        docargs = {
            'docs': docs,
            'info_account': data.get('info_account'),
            'format': 'cm_banks.check_format_template',
            'date_today': fields.Datetime.context_timestamp(self, timestamp=datetime.now()).strftime("%d/%m/%Y %H:%M:%S %p"),
            'fecha': data.get('fecha')
        }
        return docargs

    def get_data(self, ids):
        mcheck_ids = self.env.get('mcheck.mcheck').search([('id','in',ids),('state','in',['validated'])])
        info_account=[]
        fecha=""
        if mcheck_ids:    
            for check in mcheck_ids:
                moves_vals, total_debit, total_credit = self.get_moves(check.move_ids)
                print(round(check.total,2))
                info_account.append({
                    'bank_name': check.journal_id.name,
                    'check_number': check.number,
                    'check_date': check.date,
                    'pay_to': check.reference,
                    'total': round(check.total,2),
                    'amount_text': check.user_creator.company_id.to_word(round(check.total,2), check.user_creator.company_id.currency_id.name).upper(),
                    'moves': moves_vals,
                    'company_name': check.journal_id.company_id.name,
                    'debit_sum': total_debit,
                    'credit_sum': total_credit,
                    'doc_type': check.doc_type,
                    'show_letter': True,
                })
            for info in info_account:
                fdate = info.get('check_date')
                #fecha = datetime.strftime(fdate,'%d de %B del %Y')
                day = str(fdate.day)
                year = str(fdate.year)
                nmonth = fdate.strftime("%m")
                intmonth = int(nmonth)
                fecha = day + " de " + months[intmonth-1] + " del " + year
        else:
            raise UserError(_('El Cheque debe estar validado'))
        return {'info_account':info_account,'fecha':fecha}

    def get_moves(self,moves_ids):
        info_moves = []
        total_debit = 0
        total_credit = 0
        for moves in moves_ids:
            info_moves.append({
                'cuenta': moves.account_id.name,
                'etiqueta': moves.name,
                'debit': moves.debit,
                'credit': moves.credit,
                'code': moves.account_id.code
            })
            total_debit += moves.debit
            total_credit += moves.credit
        return info_moves, total_debit, total_credit
