from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class getDataNewsletter(http.Controller):

    @http.route('/api/newsletter_data',type='http',auth='public',methods=['POST'],csrf=False)
    def newsletter_data(self, **kwargs):
        data = json.loads(request.httprequest.data)
        _logger.info("##################### Data newsletter: %s #####################", data)

        request.env['cm.newsletter.list'].sudo().create({
            'name': data.get('email', ''),
            'language': data.get('language', ''),
            'date': data.get('date', ''),
            'country': data.get('country', '')
        })

        return request.make_json_response({
            'success': True,
            'message': 'Datos recibidos'
        })