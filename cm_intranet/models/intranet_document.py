from odoo import models, fields, api

class IntranetDocument(models.Model):
    _name = 'intranet.document'
    _description = 'Portal Document'
    _order = 'sequence, id desc'

    name = fields.Char(required=True,string="Nombre")
    description = fields.Text(string="Descripcion")

    file = fields.Binary(required=True,string="Archivo")
    file_name = fields.Char(string="Nombre de archivo")

    category_id = fields.Many2one(
        'intranet.document.category',
        string='Categoria'
    )

    is_published = fields.Boolean(
        string='Publicado',
        default=False
    )

    sequence = fields.Integer(default=10,string="Secuencia")
    active = fields.Boolean(default=True,string="Activo")
    allow_download = fields.Boolean(string="Permitir descarga")

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

class IntranetDocumentCategory(models.Model):
    _name = 'intranet.document.category'
    _description = 'Document Category'
    _order = 'sequence, name'

    name = fields.Char(required=True, string="Nombre")
    sequence = fields.Integer(default=10, string="Secuencia")
    active = fields.Boolean(default=True,string="Activo")
    code = fields.Char(string="Codigo")

