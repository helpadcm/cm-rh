from odoo import fields, models


class HrResumeLine(models.Model):
    _inherit = 'hr.resume.line'
    '''
    This model add the functionality to add pdf file to the resume line
    '''

    pdf_file = fields.Binary(
        string='PDF File with the resume line',
        attachment=True,
        help='PDF file with the resume line',
        )
