# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta, date
from num2words import num2words
from babel.dates import format_date
from math import ceil,floor
from odoo import api, models, fields, _
from dateutil import parser
from dateutil.relativedelta import relativedelta

class receiptDeduction(models.AbstractModel):
    _name = 'report.cm_rrhh_management.report_deduction_receipt'
    _description = "Recibo de deduccion"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = self.get_data(data)
        docargs = {
            'data': data
        }
        return docargs


    def get_data(self,data):
        request_id = self.env['rrhh.request.loan'].browse(data.get('request_id'))
        initial_deduction_date = request_id.initial_deduction_date
        last_date = request_id.deduction_id.date_estimated_end
        initial_date = ''
        final_date = ''
        if initial_deduction_date.day <= 15:
            initial_date = "1ra "
        else:
            initial_date = "2da "

        if last_date.day <= 15:
            final_date = "1ra "
        else:
            final_date = "2da "

        initial_month_text = format_date(initial_deduction_date, "MMMM", locale='es')
        initial_date += f"""Quincena de {initial_month_text} de {initial_deduction_date.year}"""

        final_month_text = format_date(last_date, "MMMM", locale='es')
        final_date += f"""Quincena de {final_month_text} de {last_date.year}"""

        report_vals = {
            'amount': request_id.amount,
            'amount_text': self.convert_amount_text(request_id.amount),
            'fortnight_amount': request_id.fortnight_amount,
            'fortnight_text': self.convert_amount_text(request_id.fortnight_amount),
            'monthly_amount': request_id.monthly_amount,
            'monthly_amount_text': self.convert_amount_text(request_id.monthly_amount),
            'fees': request_id.fees,
            'today_date': format_date(datetime.now().date(), format="d 'de' MMMM 'de' y", locale='es'),
            'initial_date': initial_date,
            'final_date': final_date,
            'employee': request_id.employee_id.name,
            'identity': request_id.employee_id.format_identification_id
        }
        return report_vals

    def convert_amount_text(self, amount):
        amount_text = num2words(int(amount), lang='es').capitalize()
        cents = int(round((amount % 1) * 100))
        if cents == 0:
            cents_text = "lempiras exactos"
        else:
            c_text = num2words(int(cents), lang='es').lower()
            cents_text = f"""lempiras con {c_text} centavos"""
        text_amount = f"{amount_text} {cents_text}"
        return text_amount