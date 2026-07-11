# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from odoo import _, models
import time
import base64
from io import BytesIO

class reviewGuidesXLS(models.AbstractModel):
    _name = 'report.cm_cargo_handling.report_guides_reviews_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Revision de guias XLS"
    
    def generate_xlsx_report(self, workbook, data, lines): 	
        xdata, total_amount = self.get_data(data)
        # xvals = xdata.get('vals')
        # xinfo = xdata.get('data')
        # xmove = xdata.get('data_move')
        sheet = workbook.add_worksheet()
        
        #titles
        format212 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False})
        format213 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': True, 'top': True, 'bold': True})
        format214 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format215 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#dadada',})
        format216 = workbook.add_format({'font_size': 13, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format217 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': True,'bottom': True, 'top': False, 'bold': True})
        format218 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': True, 'top': False, 'bold': True})
        format219 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format220 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format511 = workbook.add_format({'font_size': 12, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        #numbers
        format41 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': ' #,###,##0.00'})

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
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(10, 10, 15)
        pos=1
        
        pos_image = "B"+str(pos)
        image_data = BytesIO(base64.b64decode(self.env.user.company_id.logo))
        sheet.insert_image(pos_image,'logo',{'image_data':image_data,'x_scale': 0.1,'y_scale': 0.1,'x_offset':50})
        title_line = "B" + str(pos) + ":" + "H" + str(pos)
        sheet.merge_range(title_line, _('REVISION DE GUIAS'), format216)  
        sheet.write(pos + 1, 4, _('Desde: %s')%(data.get('initial_date')), format219)
        sheet.write(pos + 1, 5, _('Al: %s')%(data.get('final_date')), format219)
        pos+=4

        
        sheet.write(pos-1, 9, "TOTAL", format214)
        sheet.write_number(pos-1, 10, total_amount, format211)

        sheet.write(pos, 0, _('#'), format213)
        sheet.write(pos, 1, _('Numero Manifiesto'), format213)
        sheet.write(pos, 2, _('Estado Manifiesto'), format213)
        sheet.write(pos, 3, _('Numero Orden'), format213)
        sheet.write(pos, 4, _('Estado Orden'), format213)
        sheet.write(pos, 5, _('Numero Guia'), format213)
        sheet.write(pos, 6, _('Estado Guia'), format213)
        sheet.write(pos, 7, _('Numero Factura'), format213)
        sheet.write(pos, 8, _('Estado Factura'), format213)
        sheet.write(pos, 9, _('Peso'), format213)
        sheet.write(pos, 10, _('Valor'), format213)
        pos+=1
        cont = 1
        for o in xdata:
            sheet.write(pos, 0, cont, format21)
            sheet.write(pos, 1, o.get('manifest'), format212)
            sheet.write(pos, 2, o.get('manifest_state') or '', format212)
            sheet.write(pos, 3, o.get('order_number'), format212)
            sheet.write(pos, 4, o.get('order_state'), format212)
            sheet.write(pos, 5, o.get('guide_name'), format212)
            sheet.write(pos, 6, o.get('state'), format212)
            sheet.write(pos, 7, o.get('invoice'), format212)
            sheet.write(pos, 8, o.get('payment_state'), format212)
            sheet.write_number(pos, 9, o.get('weight'), format41)
            sheet.write_number(pos, 10, o.get('amount'), format41)
            pos += 1
            cont += 1


    def get_data(self, data):
        bill_obj = self.env['cargo.bill']
        initial_date = data.get('initial_date')
        final_date = data.get('final_date')
        bill_ids = bill_obj.search([('create_date','>=',initial_date),('create_date','<=',final_date)])
        data = []
        total_amount = 0
        for guide in bill_ids:
            modality = guide._fields['modality'].convert_to_export(guide.modality, guide)

            manifest = ''
            manifest_state = ''
            if guide.cargo_manifest_id:
                manifest = guide.cargo_manifest_id.name
                manifest_state = guide.cargo_manifest_id._fields['state'].convert_to_export(guide.cargo_manifest_id.state, guide.cargo_manifest_id)
            else:
                if guide.bill_log_ids:
                    line_ids = guide.bill_log_ids
                    if line_ids:
                        line_id = max(line_ids)
                        manifest = line_id.manifest_id.name
                        manifest_state = line_id.manifest_id._fields['state'].convert_to_export(line_id.manifest_id.state, line_id.manifest_id)

            vals = {
                'manifest': manifest,
                'manifest_state': manifest_state,
                'order_number': guide.order_id.name,
                'order_state': guide.order_id._fields['state'].convert_to_export(guide.order_id.state, guide.order_id),
                'guide_name': guide.name,
                'state': guide._fields['state'].convert_to_export(guide.state, guide),
                'weight': guide.weight,
                'amount': guide.amount_total,
                'invoice': guide.order_id.move_id.name or '',
                'payment_state': guide.order_id.move_id._fields['payment_state'].convert_to_export(guide.order_id.move_id.payment_state, guide.order_id.move_id),
            }
            total_amount += guide.amount_total
            data.append(vals)
        return data, total_amount