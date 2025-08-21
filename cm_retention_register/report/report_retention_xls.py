from datetime import datetime, timedelta
import time
from odoo import models, _
import time


class reportRetentionXLS(models.AbstractModel):
    _name = 'report.cm_retention_register.ret_retentions_report_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Resumen de retiros de retenciones"


    def get_lines(self, data, docids):
        report_ob = self.env.get('report.cm_retention_register.ret_report_retention')
        vals=report_ob.render_xls( data)
        return vals
    
    def generate_xlsx_report(self, workbook, data, lines): 	
        info=self.get_lines(data,lines)
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False, 'bg_color': '#dadada'})
        format111 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#dadada'})
        format21 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False})
        format211 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format212 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#dadada'})
        {}
        format41 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': '#,###,##0.00'})
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
        format211.set_text_wrap()
        
        info_data    = info.get('data')
        total_values = info.get('vals')
        company_symbol = total_values.get('company_id').currency_id.symbol
        report_name  = _(total_values.get('company_name'))
        header_name  = _(total_values.get('company_header'))
        company_rtn  =  _(total_values.get('company_rtn'))

        format42 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': '#,###,##0.00 ' + company_symbol})
        format43 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': '#,###,##0.00 ' + company_symbol})
        format44 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False, 'bg_color': '#dadada' ,'num_format': '#,###,##0.00 ' + company_symbol})
        #########TITULOS
        sheet.merge_range('G1:L1', _("WITHHOLDING RECORD"), format1)
        if total_values.get('date_start') and total_values.get('date_to'):
            sheet.merge_range('G2:L2', _('%s - %s')%(total_values.get('date_start'),total_values.get('date_to')), format1)
        else:
            sheet.merge_range('G2:L2', _('-'), format1)
        sheet.merge_range('G3:L3', report_name.upper(), format1)
        sheet.merge_range('G4:L4', company_rtn, format1)
        sheet.set_column(1, 1, 3)
        sheet.set_column(8, 8, 10)
        sheet.set_column(6,6, 20)
        sheet.set_column(10, 10, 10)
        sheet.set_column(0, 0, 13)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 30)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 16)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 8, 20)
        sheet.set_column(10, 10, 20)
        sheet.set_column(11, 11, 12)
        sheet.set_column(12, 12, 12)
        sheet.set_column(13, 13, 12)
        sheet.set_column(14, 14, 12)
        sheet.set_column(15, 15, 15)
        sheet.set_column(16, 16, 12)
        sheet.set_column(17, 17, 12)
        sheet.set_column(18, 18, 12)
        sheet.set_column(19, 19, 12)
        pos=9
        #option=xlines.get('option',{})
        #########"TITULOS LINEA"   	
        sheet.merge_range('B7:B9', _('No'), format211)
        sheet.merge_range('C7:C9', _('No. CORRELATIVO DEL COMPROBANTE DE RETENCIÓN'), format211)
        sheet.merge_range('D7:D9', _('FECHA DE EMISION DE VENCIMIENTO DE RECUPERACION'), format211)
        sheet.merge_range('E7:E9', _('APELLIDO Y NOMBRE, MOTIVO O DENOMINACIÓN SOCIAL'), format211)
        sheet.merge_range('F7:F9', _('RTN DEL RETENIDO'), format211)
        sheet.merge_range('G7:G9', _('CLAVE DE AUTORIZACIÓN DE IMPRESIÓN'), format211)


        sheet.merge_range('H7:O7', _('DATOS DEL COMPROBANTE DE VENTA QUE SUSTENTA TRANSACCIÓN'), format211)
        sheet.merge_range('H8:H9', _('FECHA DE EMISION DEL COMPROBANTE DE VENTA'), format211)
        sheet.merge_range('I8:I9', _('NÚMERO FACTURA DEL COMPROBANTE'), format211)
        sheet.merge_range('J8:J9', _('CLAVE DE AUTORIZACIÓN DE IMPRESIÓN CAI'), format211)
        sheet.merge_range('K8:K9', _('CODIGO DE AUTORIZACIÓN DE EMISION ELECTRONICA (SI APLICA)'), format211)

        sheet.merge_range('L8:O8', _('VALOR DEL COMPROBANTE'), format211)
        sheet.write(8, 11, "1%", format211)
        sheet.write(8, 12, "10%", format211)
        sheet.write(8, 13, "12.5%", format211)
        sheet.write(8, 14, "25%", format211)

        sheet.merge_range('P7:P9', _('DESCRIPCIÓN DEL TRIBUTO RETENIDO'), format211)
        sheet.merge_range('Q7:T7', _('TARIFA TASA O PORCENTAJE DE LA RETENCIÓN 1%, 10%, 12.5%, 25% Y TOTAL RETENIDO'), format211)
        sheet.merge_range('Q8:Q9', "1%", format211)
        sheet.merge_range('R8:R9', "10%", format211)
        sheet.merge_range('S8:S9', "12.5%", format211)
        sheet.merge_range('T8:T9', "25%", format211)

        count = 1
        for a in info_data:
            sheet.write(pos, 1, count, format21)
            anulated_text = "D"+str(pos+1)+":"+"N"+str(pos+1)
            if a.get('state2') == 'close':
                sheet.write(pos, 2, a.get('document_number'), format21)
                sheet.write(pos, 3, a.get('document_date'), format21)
                sheet.write(pos, 4, a.get('names'), format21)
                sheet.write(pos, 5, a.get('rtn'), format21)
                sheet.write(pos, 6, a.get('retention_cai'), format21)
                sheet.write(pos, 7, a.get('invoice_date'), format21)
                sheet.write(pos, 8, a.get('invoice_number'), format21)
                sheet.write(pos, 9, a.get('invoice_cai'), format21)
                sheet.write_number(pos, 11, a.get('amounts').get('base_1'), format43)
                sheet.write_number(pos, 12, a.get('amounts').get('base_10'), format43)
                sheet.write_number(pos, 13, a.get('amounts').get('base_12'), format43)
                sheet.write_number(pos, 14, a.get('amounts').get('base_25'), format43)
                sheet.write_number(pos, 16, a.get('amounts').get('amount_1'), format43)
                sheet.write_number(pos, 17, a.get('amounts').get('amount_10'), format43)
                sheet.write_number(pos, 18, a.get('amounts').get('amount_12'), format43)
                sheet.write_number(pos, 19, a.get('amounts').get('amount_25'), format43)
                pos+=1

            if a.get('state2') == 'cancel':
                sheet.write(pos, 2, a.get('document_number'), format11)
                sheet.merge_range(anulated_text, _("ANULADO"), format111)
                sheet.write_number(pos, 14, 0, format44)
                sheet.write(pos, 15, '', format111)
                sheet.write(pos, 16, '', format111)
                sheet.write(pos, 17, '', format111)
                sheet.write(pos, 18, '', format111)
                sheet.write_number(pos, 19, 0, format44)
                pos+=1
            count+=1
        sheet.write(pos, 10, _('TOTALES'), format21)
        sheet.write_number(pos, 11, total_values.get('total_base1'), format42)
        sheet.write_number(pos, 12, total_values.get('total_base10'), format42)
        sheet.write_number(pos, 13, total_values.get('total_base12'), format42)
        sheet.write_number(pos, 14, total_values.get('total_base25'), format42)
        sheet.write_number(pos, 16, total_values.get('total_amount1'), format42)
        sheet.write_number(pos, 17, total_values.get('total_amount10'), format42)
        sheet.write_number(pos, 18, total_values.get('total_amount12'), format42)
        sheet.write_number(pos, 19, total_values.get('total_amount25'), format42)