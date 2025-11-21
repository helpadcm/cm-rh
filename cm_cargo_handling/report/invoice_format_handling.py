from odoo import models,api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from reportlab.graphics import renderPM
from base64 import b64encode
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Drawing
from reportlab.lib import units

class invHandling(models.AbstractModel):
    _name = 'report.cm_cargo_handling.invoice_format_handling'
    _description = "Formato Factura"
 
    @api.model
    def _get_report_values(self, docids, data=None):
        move_ids = self.env['account.move'].browse(docids)
        order_ids = move_ids.mapped('order_handling_id')
        return {
            'child_guide': 'cm_cargo_handling.guide_invoice',
            'invoice_order': 'cm_cargo_handling.invoice_format_handling2',
            'data': self.get_data(order_ids),
        }

    def get_data(self, order_ids):
        order_id = self.env['sale.order.handling'].browse(order_ids.ids)

        datas = []
        for order in order_id:
            print_inv = False
            if order.move_id:
                print_inv = True

            if order.move_id.invoice_line_ids.tax_ids.amount == 0.00:
                excento = order.amount_untaxed
                gravado = 0.00
            else:
                excento = 0.00
                gravado = order.amount_untaxed

            guides_values = []
            count = 1
            for guide in order.bill_lading_ids:
                guides_values.append({
                    'number': guide.name,
                    'weight': guide.weight,
                    'qty': guide.qty,
                    'volumen': guide.volumen,
                    'barcode': self.get_image(guide.name),
                    'category': guide.product_id.name,
                    'uom_name': guide.product_id.uom_id.name,
                    'num_piece': count,
                    'description': guide.content_description
                })
                count += 1

            partner = order.partner_id
            if order.parent_id:
                partner = order.parent_id

            description_list = []
            category_list = []
            for car in order.cart_ids:
                description_list.append(car.piece_description)
                category_list.append(car.product_id.name)

            discount_amount = 0
            discount_name = False
            if order.discount_id:
                if order.discount_id.code not in ['COMAIL','G10']:
                    discount_amount = order.discount
                    discount_name = order.discount_id.name

            invoice_date = order.move_id.invoice_date or order.date

            values = {
                'company': order.user_id.company_id,
                'address_send': order.destination_id.address_send or order.destination_id.address,
                'destination_code': order.destination_id.ref,
                'order': order.name,
                'sender_name': order.sender_id.name,
                'sender_phone': order.sender_phone,
                'id_sender': order.id_sender,
                'origin': order.origin_id.ref,
                'origin_name': order.origin_id.name,
                'date': self.change_format2(order.date),
                'receiver_name': order.receiver_id.name,
                'receiver_phone': order.receiver_phone,
                'id_receiver': order.id_receiver,
                'user_name': order.user_id.name,
                'observations': order.observations or '',
                'guides': ', '.join([guide.name for guide in order.bill_lading_ids]),
                'payment_state': order.payment_state,
                'description': 'Envio de orden %s'%order.name,
                'mother_description': ', '.join([desc for desc in set(description_list)]) or '',
                'mother_product': ', '.join([cat for cat in set(category_list)]),
                'product': order.product_id.name,
                'modality': order.modality,
                'image_description': order.content_description_ids,
                'pieces': order.pieces_qty,
                'print_invoice': print_inv,

                'weight': order.weight,
                'subtotal': order_id.preliminar_price + order_id.additional_costs,
                'conv_subtotal': self.conv_amount(order.external_currency_id, order.local_currency_id, invoice_date, order.total),
                'gravado': gravado,
                'conv_gravado': self.conv_amount(order.external_currency_id, order.local_currency_id, invoice_date, gravado),
                'excento': excento,
                'conv_excento': self.conv_amount(order.external_currency_id, order.local_currency_id, invoice_date, excento),
                'taxes': order.amount_tax,
                'conv_taxes': self.conv_amount(order.external_currency_id, order.local_currency_id, invoice_date, order.amount_tax),
                'total': order.amount_total,
                'conv_total': order.move_id.amount_total_signed,
                'name_currency': order.external_currency_id.name,
                'exonerado': 0,
                'discount': discount_amount,
                'discount_name': discount_name,
                'rate': order.move_id.currency_rate,
                'amount_text': order.move_id.amount_in_words,

                'guides_values': guides_values,
                'qty_guides': order.qty_guides,

                'invoice_date': self.change_format(order.move_id.invoice_date),
                'invoice_number': order.move_id.name,
                'invoice_payment_term': order.move_id.invoice_payment_term_id.name or '',
                'invoice_date_due': self.change_format(order.move_id.invoice_date_due),
                'invoice_partner_identity': order.move_id.partner_id.identity or '',
                'invoice_partner_rtn': order.move_id.rtn_name or order.rtn or '',
                'invoice_partner_name': order.move_id.partner_name or order.client_name or partner.name,
                'invoice_partner_stree': partner.street,
                'invoice_partner_stree2': partner.street2,
                'invoice_partner_city': partner.city,
                'invoice_partner_state': partner.state_id.name,
                'invoice_partner_country': partner.country_id.name,
                'invoice_cai_shot': order.move_id.cai_number,
                'invoice_expire_cai': self.change_format(order.move_id.expiration_cai_date),
                'invoice_min_cai': order.move_id.min_number_cai,
                'invoice_max_cai': order.move_id.max_number_cai,
                'invoice_exempt_purchase': order.move_id.purchase_order_exempt or '',
                'invoice_exonerated_record': order.move_id.record_exonerated or '',
                'invoice_reg_sag': order.move_id.sag_record or '',
            }
            datas.append(values)
        return datas

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