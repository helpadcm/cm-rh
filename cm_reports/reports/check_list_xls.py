
from datetime import datetime, timedelta
from odoo import models, _
import time
from odoo import _
import time

class CheckListXls(models.AbstractModel):
    _name = 'report.cm_reports.check_list_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Reporte de Cheques XLS"

    def get_data(self, data, docids):
        report_ob=self.env.get('report.cm_reports.report_check_list')
        docargs = report_ob.render_xls( docids, data=data)
        return docargs
    
    def generate_xlsx_report(self, workbook, data, lines): 	
        xdata=self.get_data(data,lines)
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
        format111 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': False})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False})
        format211 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format212 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        {}
        format42 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': '#,###,##0.00'})
        format411 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': 'L #,###,##0.#0'})
        format412 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format':  '#,###,##0.#0'})
        format51 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': 'L #,###,##0.#0'})
        format511 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': 'L #,###,##0.#0'})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
                                    'bg_color': 'red'})
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
        format3.set_align('center')
        font_size_8.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        
        #########TITULOS
        sheet.merge_range('A3:L3', _('LISTA DE CHEQUES'), format1)
        
        sheet.set_column(0, 0, 10)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 26)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 16)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 10)
        sheet.set_column(8, 8, 10)
        sheet.set_column(10, 10, 10)
        pos=5
        
        #########"TITULOS LINEA"   	
        sheet.write(pos, 1, _('Número'), format211)
        sheet.write(pos, 2, _('Beneficiario'), format211)
        sheet.write(pos, 3, _('Asunto'), format211)
        sheet.write(pos, 4, _('Diario'), format211)
        sheet.write(pos, 5, _('Cuenta Bancaria'), format211)
        sheet.write(pos, 6, _('Monto'), format211)
        sheet.write(pos, 7, _('Fecha'), format211)
        sheet.write(pos, 8, _('Estado'), format211)
        
        pos+=1
        for line in xdata.get('info_report'):
            format41 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format':  line.get('currency') + ' #,###,##0.00'})
            sheet.write(pos, 1, line.get('number'), format21)
            sheet.write(pos, 2, line.get('beneficiary',''), format21)
            sheet.write(pos, 3, line.get('affair'), format21)
            sheet.write(pos, 4, line.get('journal'), format21)
            sheet.write(pos, 5, line.get('bank_account') or '', format21)
            sheet.write_number(pos, 6, line.get('amount'), format41)
            sheet.write(pos, 7, line.get('date'), format21)
            sheet.write(pos, 8, line.get('state'), format21)
            pos+=1