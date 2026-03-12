from odoo import models,api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from reportlab.graphics import renderPM
from base64 import b64encode
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Drawing
from reportlab.lib import units

class dailySales(models.AbstractModel):
    _name = 'report.cm_cargo_handling.daily_sales_report'
    _description = "Ventas Diarias"
 
    @api.model
    def _get_report_values(self, docids, data=None):
        info = self.get_data(data)
        initial_date_obj = datetime.strptime(data.get('initial_date'), "%Y-%m-%d")
        final_date_obj = datetime.strptime(data.get('final_date'), "%Y-%m-%d")
        formated_initial_date = initial_date_obj.strftime("%d/%m/%Y")
        formated_final_date = final_date_obj.strftime("%d/%m/%Y")
        return {
            'data': info,
            'initial_date': formated_initial_date,
            'final_date': formated_final_date,
        }

    def get_data(self, data):
        bill_obj = self.env['cargo.bill']
        initial_date = data.get('initial_date')
        final_date = data.get('final_date')

        origin_id = data.get('origin_id')
        destination_id = data.get('destination_id')

        domain = [('create_date','>=',initial_date),('create_date','<=',final_date),('modality','in',['upon_delivery','counted']),('state','not in',['desechada','canceled'])]
        if origin_id and destination_id:
            domain.append(('origin_id','=',origin_id))
            domain.append(('destination_id','=',destination_id))
        elif origin_id and not destination_id:
            domain.append(('origin_id','=',origin_id))
        elif not origin_id and destination_id:
            domain.append(('destination_id','=',destination_id))

        bill_ids = bill_obj.search(domain)
        
        datas = []
        origin_ids = []
        for bill in bill_ids:
            if not bill.order_id.discount_id or bill.order_id.discount_id.code != 'COMAIL':
                paid_counted_amount = 0
                pending_counted_amount = 0
                paid_upon_amount = 0
                pending_upon_amount = 0
                modality = bill._fields['modality'].convert_to_export(bill.modality, bill)
                state = bill._fields['state'].convert_to_export(bill.state, bill)
                payment_state = 'Sin pago'

                if bill.order_id.move_id:
                    payment_state = bill.order_id.move_id._fields['payment_state'].convert_to_export(bill.order_id.move_id.payment_state, bill.order_id.move_id)

                    if bill.order_id.move_id.payment_state == 'paid':
                        if bill.modality == 'counted':
                            paid_counted_amount = bill.order_id.move_id.amount_total
                            pending_counted_amount = 0
                        else:
                            paid_upon_amount = bill.order_id.move_id.amount_total
                            pending_upon_amount = 0
                    else:
                        if bill.modality == 'counted':
                            paid_counted_amount = bill.order_id.move_id.amount_total - bill.order_id.move_id.amount_residual
                            pending_counted_amount = bill.order_id.move_id.amount_residual
                        else:
                            paid_upon_amount = bill.order_id.move_id.amount_total - bill.order_id.move_id.amount_residual
                            pending_upon_amount = bill.order_id.move_id.amount_residual
                else:
                    pending_upon_amount = bill.amount_total

                values = {
                    'guide': bill.name,
                    'client': bill.order_id.partner_id.name,
                    'destination': bill.destination_id.ref,
                    'modality': modality,
                    'amount': bill.amount_total,
                    'payment_state': payment_state,
                    'state': state,
                }


                if bill.origin_id.id in origin_ids:
                    if bill.modality == 'counted':
                        datas[origin_ids.index(bill.origin_id.id)]['counted_guides'].append(values)
                        datas[origin_ids.index(bill.origin_id.id)]['counted_totals'] += bill.amount_total
                        datas[origin_ids.index(bill.origin_id.id)]['paid_counted_amount'] += paid_counted_amount
                        datas[origin_ids.index(bill.origin_id.id)]['pending_counted_amount'] += pending_counted_amount
                    else:   
                        datas[origin_ids.index(bill.origin_id.id)]['upon_delivery_guides'].append(values)
                        datas[origin_ids.index(bill.origin_id.id)]['upon_delivery_total'] += bill.amount_total
                        datas[origin_ids.index(bill.origin_id.id)]['paid_upon_amount'] += paid_upon_amount
                        datas[origin_ids.index(bill.origin_id.id)]['pending_upon_amount'] += pending_upon_amount
                else:
                    origin_ids.append(bill.origin_id.id)
                    vals = {
                        'origin_name': bill.origin_id.ref,
                        'paid_counted_amount': paid_counted_amount,
                        'pending_counted_amount': pending_counted_amount,
                        'paid_upon_amount': paid_upon_amount,
                        'pending_upon_amount': pending_upon_amount
                    }
                    

                    if bill.modality == 'counted':
                        vals.update({'counted_guides': [values], 'upon_delivery_guides': [], 'counted_totals': bill.amount_total, 'upon_delivery_total': 0})
                    else:
                        vals.update({'counted_guides': [], 'upon_delivery_guides': [values], 'counted_totals': 0, 'upon_delivery_total': bill.amount_total})
                    datas.append(vals)
        return datas

    def change_format(self,date):
        if date:
            formato_fecha = "%d/%m/%Y"
            # fecha_inicial = datetime.strptime(date, "%Y-%m-%d")
            fecha = datetime.strftime(date,formato_fecha)
            return fecha