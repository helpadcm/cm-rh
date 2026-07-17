from odoo import models,api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from reportlab.graphics import renderPM
from base64 import b64encode
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.graphics.shapes import Drawing
from reportlab.lib import units

class dailySalesAgent(models.AbstractModel):
    _name = 'report.cm_cargo_handling.daily_sales_agent'
    _description = "Ventas Diarias"
 
    @api.model
    def _get_report_values(self, docids, data=None):
        info = self.get_data(data)
        initial_date_obj = datetime.strptime(data.get('date'), "%Y-%m-%d")
        formated_initial_date = initial_date_obj.strftime("%d/%m/%Y")
        return {
            'data': info,
            'date': formated_initial_date
        }

    def get_data(self, data):

        datas = []
        return datas

    def change_format(self,date):
        if date:
            formato_fecha = "%d/%m/%Y"
            # fecha_inicial = datetime.strptime(date, "%Y-%m-%d")
            fecha = datetime.strftime(date,formato_fecha)
            return fecha