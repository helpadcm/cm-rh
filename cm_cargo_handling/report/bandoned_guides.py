from odoo import models,api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from reportlab.graphics import renderPM
from base64 import b64encode
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Drawing
from reportlab.lib import units

class abandonedGuides(models.AbstractModel):
    _name = 'report.cm_cargo_handling.abandoned_guides_report'
    _description = "Guias abandonadas"
 
    @api.model
    def _get_report_values(self, docids, data=None):
        info, abandoned_date = self.get_data(data)
        date_obj = datetime.strptime(data.get('initial_date'), "%Y-%m-%d")
        formated_date = date_obj.strftime("%d/%m/%Y")
        return {
            'data': info,
            'report_date': formated_date,
            'abandoned_date': abandoned_date
        }

    def get_data(self, data):
        bill_ids = self.env['cargo.bill'].search([('state','=','received')])
        actual_date = datetime.now() - timedelta(hours=6)
        new_date = actual_date - relativedelta(months=2)
        datas = []
        destination_ids = []
        for bill in bill_ids:
            if bill.bill_log_ids:
                line_id = bill.bill_log_ids.filtered(lambda line: line.type == 'received')
                if line_id:
                    line_id = max(line_id)
                    if line_id.create_date <= new_date:
                        modality = bill._fields['modality'].convert_to_export(bill.modality, bill)
                        values = {
                            'received_date': self.change_format(line_id.create_date),
                            'guide': bill.name,
                            'sender_name': bill.sender_name,
                            'id_sender': bill.id_sender,
                            'sender_phone': bill.sender_phone,
                            'receiver_name': bill.receiver_name,
                            'id_receiver': bill.id_receiver,
                            'receiver_phone': bill.receiver_phone,
                            'origin': bill.origin_id.ref,
                            'destination': bill.destination_id.ref,
                            'amount': bill.amount_total,
                            'modality': modality
                        }
                        if bill.destination_id.id in destination_ids:
                            datas[destination_ids.index(bill.destination_id.id)]['guides'].append(values)
                        else:
                            destination_ids.append(bill.destination_id.id)
                            datas.append({
                                'destination_name': bill.destination_id.ref,
                                'guides': [values]
                            })
        return datas, self.change_format(new_date)

    def change_format(self,date):
        if date:
            formato_fecha = "%d/%m/%Y"
            # fecha_inicial = datetime.strptime(date, "%Y-%m-%d")
            fecha = datetime.strftime(date,formato_fecha)
            return fecha