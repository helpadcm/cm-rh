from odoo import http
from odoo.http import request


class MobileAppController(http.Controller):

    @http.route(
        '/applink/cm',
        auth='public',
        website=True,
        type='http'
    )
    def mobile_app(self, **kw):
        return request.render(
            'cm_newsletter.mobile_app_page'
        )

    @http.route('/qr/image/<int:record_id>', type='http', auth='user')
    def qr_image(self, record_id, **kw):
        record = request.env['qr.generator'].sudo().browse(record_id)

        base = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = f"{base}/app/cm"

        return request.redirect(
            f"/report/barcode/?type=QR&value={quote(url)}&width=300&height=300"
        )