from odoo import models
import base64
import io

class templeateIncDedXlsx(models.AbstractModel):
    _name = 'report.hr_payroll_cm.template_inc_ded_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Plantilla de ingresos y deducciones de empleados"

    def generate_xlsx_report(self, workbook, data, docids):
        sheet = workbook.add_worksheet('Plantilla Ingresos y Deducciones')

        # Formatos
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        header_format = workbook.add_format({'font_size': 10, 'bold': True, 'align': 'center', 'bg_color': '#58D68D', 'color': '#000000', 'border': 2, 'text_wrap':True})
        dept_format = workbook.add_format({'font_size': 12, 'bold': True, 'align': 'center', 'bg_color': '#58D68D', 'right': True, 'left': True})
        dept_name_format = workbook.add_format({'font_size': 12, 'bold': True, 'align': 'center', 'bg_color': '#58D68D', 'border': 1})
        money_format = workbook.add_format({'font_size': 10, 'num_format': '#,##0.00','text_wrap':True,'right': True, 'left': True})
        totals_format = workbook.add_format({'font_size': 10, 'border': 1, 'bold': True, 'num_format': '#,##0.00', 'bg_color': '#58D68D'})
        count_format = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True, 'right': True, 'left': True, 'color': '#FF0000'})
        total_totals_format = workbook.add_format({'font_size': 10, 'border': 1, 'bold': True, 'num_format': '#,##0.00', 'bg_color': '#58D68D'})

        count_format.set_align('center')
        header_format.set_align('center')
        header_format.set_align('vcenter')
        format1.set_align('center')

        # Columnas base
        headers = [
            'Empleado', 'Descripcion', 'Tipo', 'Fecha de Inicio', 'Fecha de Finalizacion', 'Monto Quincenal',
            'Monto Total', 'Cuotas', 'Cuota Fija'
        ]
        column = 0
        sheet.set_column(0, 0, 35)
        sheet.set_column(1, 1, 35)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        # Escribir encabezados
        for col, header in enumerate(headers):
            sheet.write(column, col, header, header_format)
            
