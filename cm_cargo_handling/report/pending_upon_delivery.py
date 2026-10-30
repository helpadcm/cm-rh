# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from odoo import _, models
import time
import base64
from io import BytesIO

class pendingUponDeliveryXLS(models.AbstractModel):
    _name = 'report.cm_cargo_handling.report_pending_upon_delivery_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Guias por cobrar pendientes XLS"
    
    def generate_xlsx_report(self, workbook, data, lines): 	
        xdata = self.get_data(data)
        sheet = workbook.add_worksheet()
        
        #titles
        format212 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False})
        format213 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': True, 'top': True, 'bold': True})
        format214 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format215 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#dadada',})
        format216 = workbook.add_format({'font_size': 13, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#dadada'})
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
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 32)
        sheet.set_column(4, 4, 30)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        pos=1
        
        pos_image = "B"+str(pos)
        image_data = BytesIO(base64.b64decode(self.env.user.company_id.logo))
        sheet.insert_image(pos_image,'logo',{'image_data':image_data,'x_scale': 0.1,'y_scale': 0.1,'x_offset':50})
        title_line = "D" + str(pos) + ":" + "H" + str(pos)
        sheet.merge_range(title_line, _('GUIAS POR COBRAR'), format216)
        sheet.write(pos + 1, 3, _('Desde: %s')%(data.get('initial_date')), format219)
        sheet.write(pos + 1, 4, _('Al: %s')%(data.get('final_date')), format219)
        pos+=4

        for dest in xdata:
            title_line = "A" + str(pos + 1) + ":" + "B" + str(pos + 1)
            sheet.merge_range(title_line, dest.get('destination'), format216)
            pos += 1
            sheet.write(pos, 0, _('#'), format213)
            sheet.write(pos, 1, _('Guia'), format213)
            sheet.write(pos, 2, _('Fecha de creacion'), format213)
            sheet.write(pos, 3, _('Remitente'), format213)
            sheet.write(pos, 4, _('Destinatario'), format213)
            sheet.write(pos, 5, _('Manifiesto'), format213)
            sheet.write(pos, 6, _('Estado'), format213)
            sheet.write(pos, 7, _('Monto'), format213)
            pos+=1
            cont = 1
            for guide in dest.get('guides'):
                sheet.write(pos, 0, cont, format21)
                sheet.write(pos, 1, guide.get('number'), format212)
                sheet.write(pos, 2, guide.get('date') or '', format212)
                sheet.write(pos, 3, guide.get('sender'), format212)
                sheet.write(pos, 4, guide.get('receiver'), format212)
                sheet.write(pos, 5, guide.get('manifest'), format212)
                sheet.write(pos, 6, guide.get('state'), format212)
                sheet.write_number(pos, 7, guide.get('amount_total'), format41)
                pos += 1
                cont += 1
            pos += 1


    def get_data(self, data):
        bill_obj = self.env['cargo.bill']
        initial_date = data.get('initial_date')
        final_date = data.get('final_date')
        bill_ids = bill_obj.search([('create_date','>=',initial_date),('create_date','<=',final_date),('modality','=','upon_delivery'),('discount_code','!=','COMAIL'),('state','not in',['abandoned','desechada','canceled'])])
        data = []
        destination = []
        guides = []
        for guide in bill_ids:
            if not guide.order_id.move_id:
                vals = {
                    'number': guide.name,
                    'date': guide.create_date.strftime('%d/%m/%Y'),
                    'sender': guide.sender_name,
                    'receiver': guide.receiver_name,
                    'amount_total': guide.amount_total,
                    'manifest': guide.cargo_manifest_id.name or '',
                    'state': guide._fields['state'].convert_to_export(guide.state, guide)
                }
                if guide.destination_id.id in destination:
                    data[destination.index(guide.destination_id.id)]['guides'].append(vals)
                else:
                    destination.append(guide.destination_id.id)
                    data.append({
                        'destination': guide.destination_id.ref,
                        'guides': [vals]
                    })
        return data