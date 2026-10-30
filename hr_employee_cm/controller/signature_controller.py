import base64
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from odoo import http
from odoo.http import request, content_disposition
from odoo.tools.misc import file_path
import tempfile

class SignatureController(http.Controller):

    @http.route('/signature/download/<int:config_id>', type='http', auth='user', website=False)
    def download_signature(self, config_id, **kwargs):
        """Genera la firma y la devuelve como un archivo descargable."""
        config = request.env['digital.sign.creator'].browse(config_id)
        conf_id = request.env['digital.sign.conf'].search([])
        if not conf_id:
            raise ValidationError("No existe plantilla para firma")

        ###################  name configuration  ##############################
        x_name_position = conf_id.x_name_position
        y_name_position = conf_id.y_name_position
        name_font_size = conf_id.name_font_size

        ###################  job configuration  ##############################
        x_job_position = conf_id.x_job_position
        y_job_position = conf_id.y_job_position
        job_font_size = conf_id.job_font_size

        ###################  mobile configuration  ##############################
        x_mobile_position = conf_id.x_mobile_position
        y_mobile_position = conf_id.y_mobile_position
        mobile_font_size = conf_id.mobile_font_size

        ###################  company phone configuration  ##############################
        x_phone_comp_position = conf_id.x_phone_comp_position
        y_phone_comp_position = conf_id.y_phone_comp_position
        phone_comp_font_size = conf_id.phone_comp_font_size

        ###################  address configuration  ##############################
        x_address_position = conf_id.x_address_position
        y_address_position = conf_id.y_address_position
        address_font_size = conf_id.address_font_size

        # Decodificar la imagen de la plantilla
        template_img_data = base64.b64decode(conf_id.sign_template)
        template_img = Image.open(BytesIO(template_img_data))

        # Crear un objeto de dibujo sobre la imagen
        draw = ImageDraw.Draw(template_img)

        # Ruta a la fuente personalizada dentro del módulo
        name_font_path = file_path("addons/hr_employee_cm/static/fonts/Montserrat-Medium.otf")
        job_font_path = file_path('addons/hr_employee_cm/static/fonts/gotham-book.ttf')

        # Cargar la fuente (puede cambiar la ruta a una fuente TTF personalizada)
        try:
            name_font = self._load_font(conf_id.name_font, conf_id.name_font_size)
            job_font = self._load_font(conf_id.job_font, conf_id.job_font_size)
            address_font = self._load_font(conf_id.address_font, conf_id.address_font_size)
            mobile_font = self._load_font(conf_id.mobile_font, conf_id.mobile_font_size)
            company_font = self._load_font(conf_id.company_font, conf_id.phone_comp_font_size)
        except IOError:
            name_font = ImageFont.load_default()
            job_font = ImageFont.load_default()
            address_font = ImageFont.load_default()
            company_font = ImageFont.load_default()
            mobile_font = ImageFont.load_default()

        # Dibujar el texto en la posición predefinida
        name_text_position = (x_name_position, y_name_position)
        job_text_position = (x_job_position, y_job_position)
        address_text_position = (x_address_position, y_address_position)
        mobile_text_position = (x_mobile_position, y_mobile_position)
        company_text_position = (x_phone_comp_position, y_phone_comp_position)
        color_hex = "#1B371F"
        name_color_rgb = self.hex_to_rgb(color_hex)

        draw.text(name_text_position, config.name, fill=self.hex_to_rgb(conf_id.name_color), font=name_font)
        draw.text(job_text_position, config.job, fill=self.hex_to_rgb(conf_id.job_color), font=job_font)
        draw.text(address_text_position, config.address or '', fill=self.hex_to_rgb(conf_id.address_color), font=address_font)
        draw.text(mobile_text_position, config.mobile or '', fill=self.hex_to_rgb(conf_id.mobile_color), font=mobile_font)
        draw.text(company_text_position, config.employee_id.company_id.phone or '', fill=self.hex_to_rgb(conf_id.company_color), font=company_font)

        # Guardar la imagen en memoria
        output = BytesIO()
        template_img.save(output, format="PNG")
        output.seek(0)

        # Devolver la imagen como una descarga
        filename = f"Firma_{config.name}.png"
        return request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'image/png'),
                ('Content-Disposition', content_disposition(filename))
            ]
        )

    def hex_to_rgb(self, hex_color):
        """Convierte un color hexadecimal a una tupla RGB."""
        hex_color = hex_color.lstrip("#")  # Elimina el "#" si está presente
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _load_font(self, font_binary, size):
        if not font_binary:
            return ImageFont.load_default()

        data = base64.b64decode(font_binary)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ttf")
        tmp.write(data)
        tmp.close()

        return ImageFont.truetype(tmp.name, size)