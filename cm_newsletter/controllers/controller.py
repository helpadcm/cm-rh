from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class getDataNewsletter(http.Controller):

    @http.route('/api/newsletter_data', type='jsonrpc',auth='public',methods=['POST'],csrf=False)
    def newsletter_data(self, **kwargs):
        data = json.loads(request.httprequest.data)
        _logger.info("user: %s")
        _logger.info("########## Data newsletter: %s ###############", data)
        email = data.get("email")
        lenguage = data.get("lenguage")
        date = data.get("date")
        country = data.get("country")

        request.env['cm.newsletter.list'].sudo().create({
            'name': email or '',
            'lenguage': lenguage or '',
            'date': date or '',
            'country': country or ''
        })

        return {
            'success': True,
            'message': 'Datos recibidos',
            'data': data
        }