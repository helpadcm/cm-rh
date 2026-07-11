from odoo import models,api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

days = [
    "Lunes", "Martes", "Miércoles",
    "Jueves", "Viernes", "Sábado", "Domingo"
]

months = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

class abandonmentGuides(models.AbstractModel):
    _name = 'report.cm_cargo_handling.abandonment_report'
    _description = "Acta de abandono"
 
    @api.model
    def _get_report_values(self, docids, data=None):
        info = self.get_data(docids)
        return info

    def get_data(self, ids):
        manifest_id = self.env['cargo.manifest'].search([('id','in',ids)])
        datas = []
        destination_ids = []
        for manifest in manifest_id:
            list_guides = []
            for guide in manifest.cargo_bill_landing_ids:
                list_guides.append({
                    'name': guide.bill_landing_id.name,
                    'sender': guide.sender_name,
                    'product': guide.bill_landing_id.product_id.name,
                    'weight': guide.weight,
                    'receiver': guide.bill_landing_id.receiver_name,
                    'destination': guide.bill_landing_id.destination_id.ref,
                    'description': guide.description
                })
            # modality = bill._fields['modality'].convert_to_export(bill.modality, bill)
            values = {
                'abandoned_date': (manifest.abandoned_date - timedelta(hours=6)).strftime('%H:%M:%S'),
                'abandoned_day_name': days[manifest.abandoned_date.weekday()],
                'abandoned_day': manifest.abandoned_date.day,
                'abandoned_month': months[manifest.abandoned_date.month],
                'abandoned_year': manifest.abandoned_date.year,
                'abandoned_members': manifest.abandoned_members,
                'abandoned_city': manifest.abandoned_city,
                'abandoned_place': manifest.abandoned_place,
                'guides': list_guides
                # 'receiver_name': bill.receiver_name,
                # 'id_receiver': bill.id_receiver,
                # 'receiver_phone': bill.receiver_phone,
                # 'origin': bill.origin_id.ref,
                # 'destination': bill.destination_id.ref,
                # 'amount': bill.amount_total,
                # 'modality': modality
            }
        # print (a)
        return values

    def change_format(self,date):
        if date:
            formato_fecha = "%d/%m/%Y"
            # fecha_inicial = datetime.strptime(date, "%Y-%m-%d")
            fecha = datetime.strftime(date,formato_fecha)
            return fecha