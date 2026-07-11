from odoo import models,api
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from reportlab.graphics import renderPM
from base64 import b64encode
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Drawing
from reportlab.lib import units

class reportInvHandling(models.AbstractModel):
    _name = 'report.cm_cargo_handling.main_template_invoice'
    _description = "Formato Factura"
 
    @api.model
    def _get_report_values(self, docids, data=None):
        # vals = self.get_data(data)
        if data.get('group_invoice_id'):
            info_vals = self.get_data_groups(data)
            docs = 1
        else:
            order_id = self.env['sale.order.handling'].browse(data.get('order_id'))
            info_vals = self.get_data(data)
            docs = order_id
        return {
            'doc_ids': docids,
            'doc_model': 'cargo.bill',
            'docs': docs,
            'invoice_order': 'cm_cargo_handling.invoice_guide',
            'data': info_vals, # Función para obtener más datos
        }

    def get_data(self, data):
        order_id = self.env['sale.order.handling'].browse(data.get('order_id'))
        print_inv = False
        if order_id.move_id:
            print_inv = True

        if order_id.move_id.invoice_line_ids.tax_ids.amount == 0.00:
            excento = order_id.amount_untaxed
            gravado = 0.00
        else:
            excento = 0.00
            gravado = order_id.amount_untaxed

        guides_values = []
        count = 1
        for guide in order_id.bill_lading_ids:
            guides_values.append({
                'number': guide.name,
                'weight': guide.weight,
                'qty': guide.qty,
                'barcode': self.get_image(guide.name),
                'category': guide.product_id.name,
                'uom_name': guide.product_id.uom_id.name,
                'num_piece': count,
                'description': guide.content_description
            })
            count += 1

        partner = order_id.partner_id
        if order_id.parent_id:
            partner = order_id.parent_id

        description_list = []
        category_list = []
        for car in order_id.cart_ids:
            description_list.append(car.piece_description)
            category_list.append(car.product_id.name)

        discount_amount = 0
        discount_name = False
        if order_id.discount_id:
            if order_id.discount_id.code not in ['COMAIL','G10']:
                discount_amount = order_id.discount
                discount_name = order_id.discount_id.name

        invoice_date = order_id.move_id.invoice_date or order_id.date
        guide_list = []
        guide_list.append({
            'order': order_id.name,
            'pieces': order_id.pieces_qty,
            'mother_description': ', '.join([desc for desc in set(description_list)]) or '',
            'gravado': gravado,
            'excento': excento,
        })

        values = {
            'company': order_id.user_id.company_id,
            'print_guides': data.get('print_guides'),
            'address_send': order_id.destination_id.address_send or order_id.destination_id.address,
            'destination_code': order_id.destination_id.ref,
            'order': order_id.name,
            'sender_name': order_id.sender_id.name,
            'sender_phone': order_id.sender_phone,
            'id_sender': order_id.id_sender,
            'origin': order_id.origin_id.ref,
            'origin_name': order_id.origin_id.name,
            'date': self.change_format2(order_id.date),
            'receiver_name': order_id.receiver_id.name,
            'receiver_phone': order_id.receiver_phone,
            'id_receiver': order_id.id_receiver,
            'user_name': order_id.user_id.name,
            'observations': order_id.observations or '',
            'guides': ', '.join([guide.name for guide in order_id.bill_lading_ids]),
            'payment_state': order_id.payment_state,
            'description': 'Envio de orden %s'%order_id.name,
            'mother_description': ', '.join([desc for desc in set(description_list)]) or '',
            'mother_product': ', '.join([cat for cat in set(category_list)]),
            'product': order_id.product_id.name,
            'modality': order_id.modality,
            'image_description': order_id.content_description_ids,
            'pieces': order_id.pieces_qty,
            'print_invoice': print_inv,

            'guide_list': guide_list,

            'weight': order_id.weight,
            'subtotal': order_id.preliminar_price + order_id.additional_costs,
            'conv_subtotal': self.conv_amount(order_id.external_currency_id, order_id.local_currency_id, invoice_date, order_id.total),
            'gravado': gravado,
            'conv_gravado': self.conv_amount(order_id.external_currency_id, order_id.local_currency_id, invoice_date, gravado),
            'excento': excento,
            'conv_excento': self.conv_amount(order_id.external_currency_id, order_id.local_currency_id, invoice_date, excento),
            'taxes': order_id.amount_tax,
            'conv_taxes': self.conv_amount(order_id.external_currency_id, order_id.local_currency_id, invoice_date, order_id.amount_tax),
            'total': order_id.amount_total,
            'conv_total': order_id.move_id.amount_total_signed,
            'name_currency': order_id.external_currency_id.name,
            'exonerado': 0,
            'discount': discount_amount,
            'discount_name': discount_name,
            'rate': order_id.move_id.currency_rate,
            'amount_text': order_id.move_id.amount_in_words,

            'guides_values': guides_values,
            'qty_guides': order_id.qty_guides,

            'invoice_date': self.change_format(order_id.move_id.invoice_date),
            'invoice_number': order_id.move_id.name,
            'invoice_payment_term': order_id.move_id.invoice_payment_term_id.name or '',
            'invoice_date_due': self.change_format(order_id.move_id.invoice_date_due),
            'invoice_partner_identity': order_id.move_id.partner_id.identity or '',
            'invoice_partner_rtn': order_id.move_id.rtn_name or order_id.rtn or '',
            'invoice_partner_name': order_id.move_id.partner_name or order_id.client_name or partner.name,
            'invoice_partner_stree': partner.street,
            'invoice_partner_stree2': partner.street2,
            'invoice_partner_city': partner.city,
            'invoice_partner_state': partner.state_id.name,
            'invoice_partner_country': partner.country_id.name,
            'invoice_cai_shot': order_id.move_id.cai_number,
            'invoice_expire_cai': self.change_format(order_id.move_id.expiration_cai_date),
            'invoice_min_cai': order_id.move_id.min_number_cai,
            'invoice_max_cai': order_id.move_id.max_number_cai,
            'invoice_exempt_purchase': order_id.move_id.purchase_order_exempt or '',
            'invoice_exonerated_record': order_id.move_id.record_exonerated or '',
            'invoice_reg_sag': order_id.move_id.sag_record or '',
        }
        return values

    def get_data_groups(self, data):
        group_invoice_id = self.env['cargo.invoice.group_guides'].browse(data.get('group_invoice_id'))

        partner = group_invoice_id.partner_id

        guide_list = []
        discount_amount = 0
        total_excento = 0
        total_gravado = 0
        subtotal = 0
        for guide in group_invoice_id.guide_ids:
            if guide.bill_id.product_id.taxes_id == 0.00:
                excento = guide.bill_id.order_id.amount_untaxed
                gravado = 0.00
            else:
                excento = 0.00
                gravado = guide.bill_id.order_id.amount_untaxed
            total_excento += excento
            total_gravado += gravado
            subtotal += guide.bill_id.order_id.preliminar_price + guide.bill_id.order_id.additional_costs

            description_list = []
            for car in guide.bill_id.order_id.cart_ids:
                description_list.append(car.piece_description)

            guide_list.append({
                'order': guide.bill_id.name,
                'pieces': guide.bill_id.order_id.pieces_qty,
                'mother_description': ', '.join([desc for desc in set(description_list)]) or '',
                'gravado': gravado,
                'excento': excento,
            })

            if guide.bill_id.order_id.discount_id:
                if guide.bill_id.order_id.discount_id.code not in ['COMAIL','G10']:
                    discount_amount = guide.bill_id.order_id.discount

        invoice_date = group_invoice_id.move_id.invoice_date

        values = {
            'company': group_invoice_id.move_id.company_id,
            'address_send': 'Oficina de Encomiendas CM Airlines',

            'guide_list': guide_list,

            'sender_name': 'Varios',
            'id_sender': '',
            'origin_name': '',
            'date': self.change_format2(group_invoice_id.date),
            'receiver_name': 'Varios',
            'id_receiver': '',
            'user_name': group_invoice_id.move_id.invoice_user_id.name,
            'modality': 'credit',

            'subtotal': subtotal,
            'taxes': group_invoice_id.move_id.amount_tax,
            'total': group_invoice_id.move_id.amount_total,
            'conv_total': group_invoice_id.move_id.amount_total_signed,
            'name_currency': 'USD',
            'exonerado': 0,
            'discount': discount_amount,
            'rate': group_invoice_id.move_id.currency_rate,
            'amount_text': group_invoice_id.move_id.amount_in_words,
            'excento': total_excento,
            'gravado': total_gravado,

            'invoice_date': self.change_format(group_invoice_id.move_id.invoice_date),
            'invoice_number': group_invoice_id.move_id.name,
            'invoice_payment_term': group_invoice_id.move_id.invoice_payment_term_id.name or '',
            'invoice_date_due': self.change_format(group_invoice_id.move_id.invoice_date_due),
            'invoice_partner_identity': partner.identity or '',
            'invoice_partner_rtn': group_invoice_id.move_id.rtn_name or '',
            'invoice_partner_name': group_invoice_id.move_id.partner_name or  partner.name,
            'invoice_partner_stree': partner.street,
            'invoice_partner_stree2': partner.street2,
            'invoice_partner_city': partner.city,
            'invoice_partner_state': partner.state_id.name,
            'invoice_partner_country': partner.country_id.name,
            'invoice_cai_shot': group_invoice_id.move_id.cai_number,
            'invoice_expire_cai': self.change_format(group_invoice_id.move_id.expiration_cai_date),
            'invoice_min_cai': group_invoice_id.move_id.min_number_cai,
            'invoice_max_cai': group_invoice_id.move_id.max_number_cai,
            'invoice_exempt_purchase': group_invoice_id.move_id.purchase_order_exempt or '',
            'invoice_exonerated_record': group_invoice_id.move_id.record_exonerated or '',
            'invoice_reg_sag': group_invoice_id.move_id.sag_record or '',
        }
        return values

    def conv_amount(self, ex_currency_id, loc_currency_id, date, total):
        amount = ex_currency_id._convert(total, loc_currency_id, self.env.company, date, True)
        return amount

    def change_format(self,date):
        if date:
            formato_fecha = "%d/%m/%Y"
            # fecha_inicial = datetime.strptime(date, "%Y-%m-%d")
            fecha = datetime.strftime(date,formato_fecha)
            return fecha

    def change_format2(self,date):
        if date:
            formato_fecha = "%d/%m/%Y %H:%M:%S"
            # fecha_inicial = datetime.strptime(date, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=6)
            fecha = datetime.strftime(date-relativedelta(hours=6),formato_fecha)
            return fecha

    def get_image(self, datos):
        if not datos:
            return False
        datos_str = str(datos)
        barcode = self.get_barcode(value=datos_str, width=600)
        
        data_png = renderPM.drawToString(barcode, fmt='PNG')
        data_base64 = b64encode(data_png)
        
        return 'data:image/png;base64,{0}'.format(data_base64.decode('utf-8')) # .decode('utf-8') es importante

    def get_barcode(self, value, width, barWidth=0.05 * units.inch, fontSize=10, humanReadable=True):
        barcode = createBarcodeDrawing('Code128', value=value, barWidth=barWidth, 
                                       fontSize=fontSize, humanReadable=humanReadable,
                                       lquiet=5, rquiet=5,
                                       top=5, bottom=5)

        drawing_width = width
        barcode_scale = drawing_width / barcode.width
        drawing_height = barcode.height * barcode_scale

        drawing = Drawing(drawing_width, drawing_height)
        drawing.scale(barcode_scale, barcode_scale)
        drawing.add(barcode, name='barcode')

        return drawing