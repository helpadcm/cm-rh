import time
from datetime import datetime, timedelta
from odoo import models, _

class retentionsReportXLS(models.AbstractModel):
    _name = 'report.cm_retention_register.retentions_report_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Resumen de retenciones"

    def get_lines(self, data, docids):
        report_ob = self.env.get('report.cm_retention_register.report_retention')
        lines, vals = report_ob.render_xls( docids, data=data)
        return lines,vals
    
    def generate_xlsx_report(self, workbook, data, lines): 	
        xlines,values=self.get_lines(data,lines)
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
        format111 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': False})
        format21 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False})
        format211 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format212 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        {}
        format41 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': '#,###,##0.00'})
        format42 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': 'L #,###,##0.00'})
        format43 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': 'L #,###,##0.00'})
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
        sheet.merge_range('A1:G1', values.get('company_name'), format1)
        sheet.merge_range('A2:G2', values.get('company_header'), format1)
        sheet.merge_range('A3:G3', _('Reporte de Retenciones'), format1)
        sheet.set_column(1, 1, 10)
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
        pos=5
        #option=xlines.get('option',{})
        #########"TITULOS LINEA"   	
        sheet.write(pos, 0, _('Tipo'), format211)
        sheet.write(pos, 1, _('RTN'), format211)
        sheet.write(pos, 2, _('Apellidos, Nombre o Razón social'), format211)
        sheet.write(pos, 3, _('Número de Documento'), format211)
        sheet.write(pos, 4, _('Fecha de Documento'), format211)
        sheet.write(pos, 5, _('Retención Base'), format211)
        sheet.write(pos, 6, _('Impuesto Retenido'), format211)
        sheet.write(pos, 7, _('Concepto de Retención'), format211)
        sheet.write(pos, 8, _('Descripción del Impuesto'), format211)

        pos+=1
        for a in xlines.get('data'):
            sheet.write(pos, 0, a.get('type'), format21)
            sheet.write(pos, 1, a.get('rtn'), format21)
            sheet.write(pos, 2, a.get('names'), format21)
            sheet.write(pos, 3, a.get('document_number'), format21)
            sheet.write(pos, 4, a.get('document_date'), format21)
            sheet.write_number(pos, 5, a.get('base'), format43)
            sheet.write_number(pos, 6, a.get('tax'), format43)
            sheet.write(pos, 7, a.get('concept'), format21)
            sheet.write(pos, 8, a.get('description'), format21)
            pos+=1
        sheet.write_number(pos, 5, values.get('total_base',0), format42)
        sheet.write_number(pos, 6, values.get('total_tax',0), format42)
        # workbook.close()