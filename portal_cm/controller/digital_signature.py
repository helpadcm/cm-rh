from odoo import http
import base64
from odoo.http import request, content_disposition
from odoo.exceptions import ValidationError
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from odoo.tools.misc import file_path

class digitalSignaturePortal(http.Controller):

    @http.route('/digitalSignature/downloadSignature', type='http', auth="user", website=True)
    def program_to_fly_portal(self, **kwargs):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)

        values = {
            'employee_name': employee_id.name,
            'job': employee_id.job_id.name,
            'address': employee_id.work_location_id.name,
            'mobile': employee_id.mobile_phone
        }
        return request.render("portal_cm.portal_download_signature", values)


    @http.route('/download_signature/submit', type='http', auth="user", methods=["POST"], website=True)
    def create_beneficiary_submit(self, **post):
        user = request.env.user
        company_id = request.env.user.company_id
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        if not employee_id:
            return "Error: No se encontró un empleado vinculado a este usuario. Verifique su configuración en Odoo."

        employee_name = post.get("employee_name")
        job = post.get("record_job")
        address = post.get("record_address")
        mobile = post.get("record_mobile")

        vals = {
            'employee_id': employee_id.id,
            'name': employee_name,
            'job': job,
            'address': address,
            'mobile': mobile
        }
        sign_creator_id = request.env['digital.sign.creator'].sudo().create(vals)
        return request.redirect(f'/signaturePortal/download/{sign_creator_id.id}')

    @http.route('/signaturePortal/download/<int:config_id>', type='http', auth='user', website=False)
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
        name_font_path = file_path("addons/hr_employee_cm/static/fonts/GothamCondensed-Bold.otf")
        job_font_path = file_path('addons/hr_employee_cm/static/fonts/gotham-book.ttf')

        # Cargar la fuente (puede cambiar la ruta a una fuente TTF personalizada)
        try:
            name_font = ImageFont.truetype(name_font_path, name_font_size)
            job_font = ImageFont.truetype(job_font_path, job_font_size)
            address_font = ImageFont.truetype(job_font_path, address_font_size)
        except IOError:
            name_font = ImageFont.load_default()
            job_font = ImageFont.load_default()
            address_font = ImageFont.load_default()

        # Dibujar el texto en la posición predefinida
        name_text_position = (x_name_position, y_name_position)
        job_text_position = (x_job_position, y_job_position)
        address_text_position = (x_address_position, y_address_position)
        mobile_text_position = (x_mobile_position, y_mobile_position)
        color_hex = "#1B371F"
        name_color_rgb = self.hex_to_rgb(color_hex)

        draw.text(name_text_position, config.name, fill=name_color_rgb, font=name_font)
        draw.text(job_text_position, config.employee_id.job_id.name or '', fill=name_color_rgb, font=job_font)
        draw.text(address_text_position, config.employee_id.work_location_id.name or '', fill="white", font=address_font)
        draw.text(mobile_text_position, config.employee_id.mobile_phone or '', fill="white", font=address_font)

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