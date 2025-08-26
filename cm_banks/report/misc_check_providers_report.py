# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
import locale
from math import ceil,floor
from odoo import api, models, fields, _
from dateutil import parser
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError,ValidationError

months=["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

class ReportChecks(models.AbstractModel):
    _name = 'report.cm_banks.payment_check_provider'
    _description = "Formato de cheque pagos proveedor"

    @api.model
    def _get_report_values(self, docids, data=None):
        account_payment = self.env.get('account.payment').search([('id','in',docids),('state','in',['posted'])])
        tipo = account_payment.mapped('journal_id')
        if len(tipo)!=1:
            raise ValidationError(_("El diario debe ser el mismo"))

        data = self.get_data(docids)
        docargs = {
            'info_account':data.get('info_account'),
            # 'format': 'cm_banks.payment_check_provider_template',
            'date_today':fields.Datetime.context_timestamp(self, timestamp=datetime.now()).strftime("%d/%m/%Y %H:%M:%S %p"),
            'fecha':data.get('fecha')
        }
        return docargs

    def get_data(self,ids):
        account_payment = self.env.get('account.payment').search([('id','in',ids),('state','in',['posted'])])
        info_account=[]
        if account_payment:    
            for check in account_payment:
                if check.move_id:
                    moves=self.get_moves(check.move_id,1)
                else:
                    moves=self.get_moves(check.move_line_ids,0)
                asiento=self.suma_debito_credito(moves)
                info_account.append({
                    'bank_name': check.journal_id.name,
                    'check_number': check.name,
                    'check_date': check.date,
                    'pay_to': check.partner_id_for_parents.name,
                    'total': check.amount,
                    'amount_text': check.company_id.to_word(check.amount, check.company_id.currency_id.name).upper(),
                    'moves': moves,
                    'company_name': check.journal_id.company_id.name,
                    'debit_sum': asiento.get('suma_debito'),
                    'credit_sum': asiento.get('suma_credito'),
                    'pay_method_type': check.pay_method_type,
                    'move': check.move_id.name,
                    'concept': check.communication,
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

    def get_moves(self,moves_ids,flag):
        info_moves = []
        if flag == 1:
            for moves in moves_ids.line_ids:
                info_moves.append({
                    'cuenta':moves.account_id.name,
                    'etiqueta':moves.name,
                    'debit':moves.debit,
                    'credit':moves.credit,
                    'code':moves.account_id.code
                })
        else:
            for moves in moves_ids:
                info_moves.append({
                    'cuenta':moves.account_id.name,
                    'etiqueta':moves.name,
                    'debit':moves.debit,
                    'credit':moves.credit,
                    'code':moves.account_id.code
                })
        return info_moves

    def suma_debito_credito(self,info):
        suma_debito = 0
        suma_credito = 0
        for i in info:
            suma_debito+=i.get('debit')
            suma_credito+=i.get('credit')
        return {'suma_debito':suma_debito,'suma_credito':suma_credito}
