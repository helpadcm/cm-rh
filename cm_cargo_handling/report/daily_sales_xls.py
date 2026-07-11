# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from odoo import _, models
import time
import base64
from io import BytesIO

class handlingVolumeXLS(models.AbstractModel):
    _name = 'report.cm_cargo_handling.daily_sales_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Ventas Diarias XLS"
    
    def generate_xlsx_report(self, workbook, data, lines): 	
        report_obj = self.env['report.cm_cargo_handling.daily_sales_report']
        info = report_obj._get_report_values(lines, data=data)
        for point in info.get('data'):
            sheet = workbook.add_worksheet(point.get('origin_name'))
            
            #titles
            format212 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False})
            format213 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': True, 'top': True, 'bold': True})
            format214 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#E5E7EB',})
            format215 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#dadada',})
            format216 = workbook.add_format({'font_size': 13, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
            format217 = workbook.add_format({'font_size': 13, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#CDCDCD',})
            format218 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': True, 'top': False, 'bold': True})
            format219 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
            format220 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
            format511 = workbook.add_format({'font_size': 12, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
            #numbers
            format41 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': '$ #,###,##0.00'})
            format42 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': '$ #,###,##0.00', 'bg_color': '#E5E7EB',})

            format1 = workbook.add_format({'font_size': 14, 'bottom': False, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
            format2 = workbook.add_format({'font_size': 14, 'bottom': False, 'right': True, 'left': True, 'top': False, 'align': 'vcenter', 'bold': True})
            format4 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': False, 'align': 'vcenter', 'bold': True})
            format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
            format111 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': False})
            format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': False,'bottom': False, 'top': False, 'bold': True})

            format211 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': True, 'left': False,'bottom': True, 'top': True, 'bold': True, 'num_format':  '#,###,##0.#0'})
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
            

            sheet.set_column(0, 0, 5)
            sheet.set_column(1, 1, 15)
            sheet.set_column(2, 2, 30)
            sheet.set_column(3, 3, 15)
            sheet.set_column(4, 4, 15)
            sheet.set_column(5, 5, 15)
            sheet.set_column(6, 6, 15)
            sheet.set_column(7, 7, 15)
            pos=1
            
            pos_image = "B"+str(pos)
            image_data = BytesIO(base64.b64decode(self.env.user.company_id.logo))
            sheet.insert_image(pos_image,'logo',{'image_data':image_data,'x_scale': 0.1,'y_scale': 0.1,'x_offset':50})
            title_line = "B" + str(pos) + ":" + "G" + str(pos)
            sheet.merge_range(title_line, _('VENTAS DIARIAS'), format216)
            sheet.write(pos, 5, _('Desde: %s')%(data.get('initial_date')), format219)
            sheet.write(pos, 6, _('Al: %s')%(data.get('final_date')), format219)

            if data.get('origin_name') and data.get('destination_name'):
                sheet.write(pos + 1, 5, _('Origen: %s')%(data.get('origin_name')), format219)
                sheet.write(pos + 1, 6, _('Destino: %s')%(data.get('destination_name')), format219)
            elif data.get('origin_name') and not data.get('destination_name'):
                sheet.write(pos + 1, 6, _('Origen: %s')%(data.get('origin_name')), format219)
            elif not data.get('origin_name') and data.get('destination_name'):
                sheet.write(pos + 1, 6, _('Destino: %s')%(data.get('destination_name')), format219)
            pos+=4

            title_origin = "A" + str(pos) + ":" + "G" + str(pos)
            sheet.merge_range(title_origin, point.get('origin_name'), format217)

            if len(point.get('counted_guides')) > 0:
                pos += 1
                title_counted = "A" + str(pos) + ":" + "B" + str(pos)
                sheet.merge_range(title_counted, "CONTADO", format216)

                title_counted = "F" + str(pos) + ":" + "G" + str(pos)
                sheet.merge_range(title_counted, f"""Pagado: $ {'{0:,.2f}'.format(point.get('paid_counted_amount'))}""", format216)
            
                sheet.write(pos, 0, _('#'), format213)
                sheet.write(pos, 1, _('Guia'), format213)
                sheet.write(pos, 2, _('Cliente'), format213)
                sheet.write(pos, 3, _('Destino'), format213)
                sheet.write(pos, 4, _('Estado'), format213)
                sheet.write(pos, 5, _('Estado de Pago'), format213)
                sheet.write(pos, 6, _('Monto'), format213)
                pos+=1
                cont = 1
                total_counted = 0
                for counted in point.get('counted_guides'):
                    sheet.write(pos, 0, cont, format21)
                    sheet.write(pos, 1, counted.get('guide'), format212)
                    sheet.write(pos, 2, counted.get('client') or '', format212)
                    sheet.write(pos, 3, counted.get('destination'), format212)
                    sheet.write(pos, 4, counted.get('state'), format212)
                    sheet.write(pos, 5, counted.get('payment_state'), format212)
                    sheet.write_number(pos, 6, counted.get('amount'), format41)
                    total_counted += counted.get('amount')
                    pos += 1
                    cont += 1
                sheet.write(pos, 5, "TOTAL", format214)
                sheet.write_number(pos, 6, total_counted, format42)
                pos += 2

            if len(point.get('upon_delivery_guides')) > 0:
                pos += 1
                title_upon = "A" + str(pos) + ":" + "B" + str(pos)
                sheet.merge_range(title_upon, "POR COBRAR", format216)

                title_counted = "D" + str(pos) + ":" + "E" + str(pos)
                sheet.merge_range(title_counted, f"""Pagado: $ {'{0:,.2f}'.format(point.get('paid_upon_amount'))}""", format216)

                title_counted = "F" + str(pos) + ":" + "G" + str(pos)
                sheet.merge_range(title_counted, f"""Pendiente: $ {'{0:,.2f}'.format(point.get('pending_upon_amount'))}""", format216)
            
                sheet.write(pos, 0, _('#'), format213)
                sheet.write(pos, 1, _('Guia'), format213)
                sheet.write(pos, 2, _('Cliente'), format213)
                sheet.write(pos, 3, _('Destino'), format213)
                sheet.write(pos, 4, _('Estado'), format213)
                sheet.write(pos, 5, _('Estado de Pago'), format213)
                sheet.write(pos, 6, _('Monto'), format213)
                pos+=1
                cont = 1
                total_upon = 0

                for upon in point.get('upon_delivery_guides'):
                    sheet.write(pos, 0, cont, format21)
                    sheet.write(pos, 1, upon.get('guide'), format212)
                    sheet.write(pos, 2, upon.get('client') or '', format212)
                    sheet.write(pos, 3, upon.get('destination'), format212)
                    sheet.write(pos, 4, upon.get('state'), format212)
                    sheet.write(pos, 5, upon.get('payment_state'), format212)
                    sheet.write_number(pos, 6, upon.get('amount'), format41)
                    total_upon += upon.get('amount')
                    pos += 1
                    cont += 1
                sheet.write(pos, 5, "TOTAL", format214)
                sheet.write_number(pos, 6, total_upon, format42)