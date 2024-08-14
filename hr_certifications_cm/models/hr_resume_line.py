import api
from odoo import fields, models


class HrResumeLine(models.Model):
    _inherit = 'hr.resume.line'
    '''
    This model add the functionality to add pdf file to the resume line
    '''

    pdf_file = fields.Binary(
        string='Archivo PDF',
        attachment=True,
        help='PDF file with the resume line',
        )

    @api.model
    def download_pdf(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/pdf_file/%s?download=true' % (self.id, self.pdf_file),
            'target': 'self',
            }
