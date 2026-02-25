# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from odoo import _, models
import time
import base64
from io import BytesIO

class discountAppliedXLS(models.AbstractModel):
    _name = 'report.cm_cargo_handling.report_discount_applied_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Descuentos aplicados XLS"
    
    def generate_xlsx_report(self, workbook, data, lines): 	
        xdata = self.get_data(data)
        # xvals = xdata.get('vals')
        # xinfo = xdata.get('data')
        # xmove = xdata.get('data_move')
        sheet = workbook.add_worksheet()
        
        #titles
        format212 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False})
        format213 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': True, 'top': True, 'bold': True})
        format214 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format215 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False, 'bg_color': '#dadada',})
        format216 = workbook.add_format({'font_size': 13, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format217 = workbook.add_format({'font_size': 13, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#000000', 'color': '#FFFFFF'})
        format218 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': True, 'top': False, 'bold': True})
        format219 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format220 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format511 = workbook.add_format({'font_size': 12, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        #numbers
        format41 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': ' #,###,##0.00'})
        format42 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': ' #,###,##0.00', 'bg_color': '#dadada'})

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
        

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 10)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 40)
        sheet.set_column(6, 6, 10)
        sheet.set_column(7, 7, 15)
        pos=1
        
        pos_image = "B"+str(pos)
        image_data = BytesIO(base64.b64decode(self.env.user.company_id.logo))
        sheet.insert_image(pos_image,'logo',{'image_data':image_data,'x_scale': 0.1,'y_scale': 0.1,'x_offset':50})
        title_line = "B" + str(pos) + ":" + "H" + str(pos)
        sheet.merge_range(title_line, _('Descuentos aplicados'), format216)  
        sheet.write(pos + 1, 4, _('Desde: %s')%(data.get('initial_date')), format219)
        sheet.write(pos + 1, 5, _('Al: %s')%(data.get('final_date')), format219)
        pos+=4

        
        if not data.get('detail'):
            for m in xdata.values():
                title_partner = "A" + str(pos + 1) + ":" + "C" + str(pos + 1)
                sheet.merge_range(title_partner, m.get('partner_name'), format217)
                pos += 1
                sheet.write(pos, 0, _('Descuento'), format213)
                sheet.write(pos, 1, _('Cant. Guias'), format213)
                sheet.write(pos, 2, _('Peso Total'), format213)
                pos += 1
                for disc in m.get('discounts').values():
                    sheet.write(pos, 0, disc.get('discount_name'), format212)
                    sheet.write_number(pos, 1, disc.get('total_guides') or 0, format41)
                    sheet.write_number(pos, 2, disc.get('total_weight') or 0, format41)
                    pos += 1
                pos += 1
        else:
            for m in xdata.values():
                title_partner = "A" + str(pos + 1) + ":" + "C" + str(pos + 1)
                sheet.merge_range(title_partner, m.get('partner_name'), format217)
                pos += 1
                sheet.write(pos, 0, _('Descuento'), format213)
                sheet.write(pos, 1, _('Cant. Guias'), format213)
                sheet.write(pos, 2, _('Peso Total'), format213)
                pos += 1
                for disc in m.get('discounts').values():
                    sheet.write(pos, 0, disc.get('discount_name'), format215)
                    sheet.write_number(pos, 1, disc.get('total_guides') or 0, format42)
                    sheet.write_number(pos, 2, disc.get('total_weight') or 0, format42)
                    pos += 1
                    sheet.write(pos, 1, _('#'), format213)
                    sheet.write(pos, 2, _('Guia'), format213)
                    sheet.write(pos, 3, _('Origen'), format213)
                    sheet.write(pos, 4, _('Destino'), format213)
                    sheet.write(pos, 5, _('Descripción'), format213)
                    sheet.write(pos, 6, _('Peso'), format213)
                    pos += 1
                    cont = 1
                    for guide in disc.get('guides'):
                        sheet.write(pos, 1, cont, format212)
                        sheet.write(pos, 2, guide.get('number'), format212)
                        sheet.write(pos, 3, guide.get('origin'), format212)
                        sheet.write(pos, 4, guide.get('destination'), format212)
                        sheet.write(pos, 5, guide.get('description'), format212)
                        sheet.write_number(pos, 6, guide.get('weight') or 0, format41)
                        pos += 1
                        cont += 1
                    pos +=1
                pos += 1


    def get_data(self, data):
        bill_obj = self.env['cargo.bill']
        initial_date = data.get('initial_date')
        final_date = data.get('final_date')
        detail = data.get('detail')
        partner_ids = data.get('partner_ids')
        if partner_ids:
            bill_ids = bill_obj.search([('create_date','>=',initial_date),('create_date','<=',final_date),('order_id.partner_id','in',partner_ids),('state','!=','canceled')])
        else:
            bill_ids = bill_obj.search([('create_date','>=',initial_date),('create_date','<=',final_date)])

        result = {}
        for guide in bill_ids:
            if guide.order_id.discount_id and not guide.order_id.partner_id.default_client:
                partner = guide.order_id.partner_id
                discount = guide.order_id.discount_id

                vals = {
                    'number': guide.name,
                    'description': guide.content_description,
                    'origin': guide.origin_id.ref,
                    'destination': guide.destination_id.ref,
                    'weight': guide.weight
                }

                # --- NIVEL PARTNER ---
                if partner.id not in result:
                    result[partner.id] = {
                        'partner': partner,
                        'partner_name': partner.name,
                        'total_weight': 0.0,
                        'total_guides': 0,
                        'discounts': {}
                    }

                result[partner.id]['total_weight'] += guide.weight
                result[partner.id]['total_guides'] += 1

                # --- NIVEL DESCUENTO ---
                discounts = result[partner.id]['discounts']

                if discount.id not in discounts:
                    discounts[discount.id] = {
                        'discount': discount,
                        'discount_name': discount.name,
                        'total_weight': 0.0,
                        'total_guides': 0,
                        'guides': []
                    }

                discounts[discount.id]['total_weight'] += guide.weight
                discounts[discount.id]['total_guides'] += 1
                discounts[discount.id]['guides'].append(vals)
        return result