import base64
from odoo import http
from odoo.http import request

class PortalIntranet(http.Controller):

    @http.route('/intranet_rrhh/documents', auth='user', website=True)
    def portal_documents(self):
        documents = request.env['intranet.document'].sudo().search([
            ('is_published', '=', True),
            ('active', '=', True),
        ])

        categories = request.env[
            'intranet.document.category'
        ].sudo().search([('active', '=', True)])

        return request.render(
            'cm_intranet.portal_documents',
            {
                'documents': documents,
                'categories': categories,
            }
        )

    @http.route('/portal/documents/<int:doc_id>/download',
                auth='user', website=True)
    def portal_document_download(self, doc_id):
        doc = request.env['intranet.document'].sudo().browse(doc_id)

        if not doc.is_published or not doc.active:
            return request.not_found()

        return request.make_response(
            base64.b64decode(doc.file),
            headers=[
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition',
                 f'attachment; filename="{doc.file_name}"')
            ]
        )

    @http.route('/portal/documents/<int:doc_id>/preview',
            auth='user', website=True)
    def portal_document_preview(self, doc_id):
        doc = request.env['intranet.document'].sudo().browse(doc_id)

        if not doc.is_published or not doc.active:
            return request.not_found()

        content_type = 'application/octet-stream'
        name = (doc.file_name or '').lower()

        if name.endswith(('.png', '.jpg', '.jpeg', '.webp')):
            content_type = 'image/*'
        elif name.endswith('.pdf'):
            content_type = 'application/pdf'

        return request.make_response(
            base64.b64decode(doc.file),
            headers=[
                ('Content-Type', content_type),
                ('Content-Disposition',
                f'inline; filename="{doc.file_name}"')
            ]
        )
