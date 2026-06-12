from odoo import models, fields, api

class internalPortalDocument(models.Model):
    _name = 'internal.portal.document'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = 'Internal Portal Document'

    name = fields.Char(required=True,string="Nombre",tracking=True)
    description = fields.Text(string="Descripcion",tracking=True)
    file = fields.Binary(string="Archivo",tracking=True)
    file_name = fields.Char(string="Nombre de archivo",tracking=True)
    category_id = fields.Many2one('internal.portal.category',string='Categoria',tracking=True)
    link = fields.Char(string="Enlace",tracking=True)

    file_type = fields.Selection(
        [
            ('image', 'Image'),
            ('pdf', 'PDF'),
            ('other', 'Other'),
        ],
        compute='_compute_file_type',
        store=False,
    )

    @api.depends('file_name')
    def _compute_file_type(self):
        for rec in self:
            name = (rec.file_name or '').lower()
            if name.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                rec.file_type = 'image'
            elif name.endswith('.pdf'):
                rec.file_type = 'pdf'
            else:
                rec.file_type = 'other'

class internalDocumentCategory(models.Model):
    _name = 'internal.portal.category'
    _description = 'Internal Portal Document Category'
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(required=True, string="Nombre", tracking=True)
    sequence = fields.Integer(default=10, string="Secuencia", tracking=True)
    code = fields.Char(string="Codigo",tracking=True)
    url_address = fields.Char(string="URL")

    def action_view_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.url_address,
            'target': 'new',
        }