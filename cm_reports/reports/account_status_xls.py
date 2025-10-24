# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from odoo import _, models
import time
import base64
from io import BytesIO

class accountStatusXLS(models.AbstractModel):
    _name = 'report.cm_reports.account_status_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Estado de Cuenta XLS"


    def get_data(self, data, docids):
        report_ob = self.env.get('report.cm_reports.report_account_status')
        info = report_ob.render_xls(docids, data=data)
        return info
    
    def generate_xlsx_report(self, workbook, data, lines): 	
        xdata = self.get_data(data, lines)
        xvals = xdata.get('vals')
        xinfo = xdata.get('data')
        xmove = xdata.get('data_move')
        sheet = workbook.add_worksheet()
        
        #titles
        format211 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format212 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False})
        format213 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': True, 'top': True, 'bold': True})
        format214 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format215 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#dadada',})
        format216 = workbook.add_format({'font_size': 13, 'align': 'center', 'right': True, 'left': True,'bottom': False, 'top': True, 'bold': True})
        format217 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': True,'bottom': True, 'top': False, 'bold': True})
        format218 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': True, 'top': False, 'bold': True})
        format219 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': True, 'left': False,'bottom': True, 'top': False, 'bold': True})
        format220 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format511 = workbook.add_format({'font_size': 12, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        #numbers
        format41 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': ' #,###,##0.00'})

        format1 = workbook.add_format({'font_size': 14, 'bottom': False, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format2 = workbook.add_format({'font_size': 14, 'bottom': False, 'right': True, 'left': True, 'top': False, 'align': 'vcenter', 'bold': True})
        format4 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': False, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
        format111 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': False})
        format21 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False})

        format411 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': 'L #,###,##0.#0'})
        format412 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format':  '#,###,##0.#0'})
        format51 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': 'L #,###,##0.#0'})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
                                    'bg_color': 'red'})
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
        format3.set_align('center')
        font_size_8.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        format2.set_align('center')
        format4.set_align('center')
        red_mark.set_align('center')
        
        #########TITULOS

        sheet.set_column(0, 0, 3)
        sheet.set_column(1, 1, 32)
        sheet.set_column(2, 2, 32)
        sheet.set_column(3, 3, 32)
        sheet.set_column(4, 4, 32)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 20)
        pos=6
        

        image_data=BytesIO(base64.b64decode(self.env.user.company_id.logo))
        for o in xinfo:
            sheet.write(pos-6, 2, o.get('company_id').name, format511)
            sheet.write(pos-5, 2, "RTN: "+ o.get('company_id').company_registry, format220)


            sheet.write(pos-6, 4, o.get('company_id').street, format220)
            sheet.write(pos-5, 4, o.get('company_id').street2, format220)
            sheet.write(pos-4, 4, o.get('company_id').city + " " + o.get('company_id').zip + " " + o.get('company_id').country_id.name, format220)
            sheet.write(pos-3, 4, "Tel. "+ o.get('company_id').phone, format220)

            format42 = workbook.add_format({'font_size': 10, 'align': 'right','right': False, 'left': False,'bottom': True, 'top': True, 'bold': True,'num_format': o.get('symbol') +' #,###,##0.00'})
            format43 = workbook.add_format({'font_size': 10, 'align': 'right','right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#dadada', 'num_format': o.get('symbol') +' #,###,##0.00'})
            pos_image = "B"+str(pos-5)
            sheet.insert_image(pos_image,'logo',{'image_data':image_data,'x_scale': 0.1,'y_scale': 0.1,'x_offset':50})
            title_line="B"+str(pos)+":"+"F"+str(pos)
            sheet.merge_range(title_line, _('ESTADO DE CUENTA'), format216)
            sheet.write(pos, 1, _('Cliente: %s')%(o.get('partner').name), format217)
            sheet.write(pos, 2, '', format218)
            sheet.write(pos, 3, f"""Quincena: {xvals.get('fortnight')}""", format218)    
            if xvals.get('date_from'):
                sheet.write(pos, 4, _('Desde: %s')%(xvals.get('date_from')), format218)
                sheet.write(pos, 5, _('Al: %s')%(xvals.get('date_to')), format219)
            else:
                sheet.write(pos, 5, _('Al %s')%(xvals.get('date_to')), format219)
            pos+=2

            sheet.write(pos, 1, _('Fecha'), format213)
            sheet.write(pos, 2, _('Reserva'), format213)
            sheet.write(pos, 3, _('Concepto'), format213)
            sheet.write(pos, 4, _('Facturado'), format213)
            sheet.write(pos, 5, _('Pagado'), format213)
            sheet.write(pos, 6, _('Saldo'), format213)
            pos+=1
            total_invoiced = 0.00
            total_payed = 0.00
            total_balance = 0.00
            for op in o.get('datas'):
                sheet.write(pos, 1, op.get('date'), format212)
                sheet.write(pos, 2, op.get('pnr') or '', format212)
                sheet.write(pos, 3, op.get('concept'), format211)
                sheet.write_number(pos, 4, op.get('invoiced_amount'), format41)
                sheet.write_number(pos, 5, op.get('paid_amount'), format41)
                sheet.write_number(pos, 6, op.get('balance'), format41)
                total_invoiced += op.get('invoiced_amount')
                total_payed += op.get('paid_amount')
                total_balance += op.get('balance')
                pos+=1
            pos+=1
            text_balance="B"+str(pos)+":"+"D"+str(pos)
            sheet.merge_range(text_balance, _('TOTAL'), format215)
            sheet.write_number(pos-1, 4, o.get('total_invoiced'), format43)
            sheet.write_number(pos-1, 5, o.get('total_payed'), format43)
            sheet.write_number(pos-1, 6, o.get('total_balance'), format43)
            pos += 2

            sheet.write(pos, 1, _('Saldo Total'), format213)
            sheet.write_number(pos, 2, o.get('total_balance'), format42)
            pos+=2

            sheet.write(pos, 1, _('BANCO'), format213)
            sheet.write(pos, 2, _('MONEDA'), format213)
            sheet.write(pos, 3, _('CUETA'), format213)
            pos+=1
            sheet.write(pos, 1, _('Bac Honduras'), format213)
            sheet.write(pos, 2, _('USD'), format213)
            sheet.write(pos, 3, _('730134921'), format213)
            pos+=1
            sheet.write(pos, 1, _('Bac Honduras'), format213)
            sheet.write(pos, 2, _('HNL'), format213)
            sheet.write(pos, 3, _('730049441'), format213)
            pos+=1
            sheet.write(pos, 1, _('Banco Ficohsa'), format213)
            sheet.write(pos, 2, _('USD'), format213)
            sheet.write(pos, 3, _('01-107-51646'), format213)
            pos+=1
            sheet.write(pos, 1, _('Banco Ficohsa'), format213)
            sheet.write(pos, 2, _('HNL'), format213)
            sheet.write(pos, 3, _('08-102-332041'), format213)
            pos+=8