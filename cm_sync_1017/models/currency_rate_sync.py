import requests
import logging
from odoo import models, fields, api
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class currencyRateSync(models.Model):
    _inherit = 'res.currency.rate'

    def sync_rate(self, opt='production'):
        currency_usd_id =  self.env.ref('base.USD')
        ip = '181.189.230.70'
        if opt == 'test':
            ip = '10.1.4.56'

        last_date = datetime.now().date()
        url = "http://%s:8000/get_rate?date=%s&currency_id=%s"%(ip, last_date, 45)
        response = requests.get(url)

        if response.status_code == 200:
            rates = response.json()
            for rat in rates:
                self.env['res.currency.rate'].create({
                    'currency_id': currency_usd_id.id,
                    'name': last_date,
                    'inverse_company_rate': rat.get('rate') 
                })