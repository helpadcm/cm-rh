# -*- coding: utf-8 -*-
from odoo import models, fields, api
from PIL import Image
try:
  import qrcode
except ImportError:
  qrcode = None
try:
  import base64
except ImportError:
  base64 = None
from io import BytesIO

class QRGenerator(models.Model):
    _name = "qr.generator"

    name = fields.Char(required=True)
    qr_url = fields.Char(compute="_compute_qr")
    qr_filename = fields.Char(default="qr_code_cm.png")
    qr_image = fields.Binary(
        string="Código QR",
        compute="_compute_qr_image"
    )

    @api.depends()
    def _compute_qr(self):
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")

        for rec in self:
            rec.qr_url = (
                f"{base}/applink/cm"
            )

    def _compute_qr_image(self):
        for rec in self:
            if qrcode and base64:
                qr = qrcode.QRCode(
                    version=None,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(rec.qr_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.qr_image = qr_image

    def download_qr(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=qr.generator&id={self.id}&field=qr_image&filename_field=qr_filename&download=true',
            'target': 'self',
        }