from odoo import fields, models


class projectInherit(models.Model):
    _inherit = 'project.project'

    is_private = fields.Boolean(string="Privado")
    follower_ids = fields.Many2many('res.users',string="Seguidores")