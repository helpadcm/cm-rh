import base64
import tempfile
from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from odoo.http import request

class digitalSignCreator(models.TransientModel):
    _name = 'digital.sign.creator'
    _description = 'Creador de firma digital'

    @api.model
    def employee_default(self):
        user_id = self.env.user.id
        employee_id = self.env['hr.employee'].search([('user_id','=',user_id)])
        if employee_id:
            return employee_id.id

    @api.model
    def name_employee_default(self):
        user_id = self.env.user.id
        employee_id = self.env['hr.employee'].search([('user_id','=',user_id)])
        if employee_id:
            return employee_id.name

    name = fields.Char('Nombre a mostrar en firma', required=True, default=name_employee_default)
    employee_id = fields.Many2one('hr.employee', string='Empleado', default=employee_default)
    job = fields.Char(string="Puesto de trabajo")
    address = fields.Char(string="Direccion")
    mobile = fields.Char(string="Telefono")

    @api.onchange("employee_id")
    def get_employee_data(self):
        if self.employee_id:
            self.job = self.employee_id.job_title
            self.address = self.employee_id.work_location_id.name
            self.mobile = self.employee_id.mobile_phone

    def action_download_sign(self):
        """Redirige al usuario a la URL del controlador para descargar la firma."""
        return {
            'type': 'ir.actions.act_url',
            'url': f'/signature/download/{self.id}',
            'target': 'self',
        }

class digitalSignConf(models.Model):
    _name = 'digital.sign.conf'
    _description = 'Configuraciones firma digital'

    name = fields.Char(string="Nombre",default="Conf. Firma digital CM Airlines")
    sign_template = fields.Binary(string="Plantilla Firma", attachment=True)
    
    ###################  name configuration  ##############################
    x_name_position = fields.Integer(string="Posicion X (Nombre)", default=865)
    y_name_position = fields.Integer(string="Posicion Y (Nombre)", default=155)
    name_font_size = fields.Integer(string="Tamaño de letra (Nombre) ", default=75)
    name_color = fields.Char(default="#1B371F",string="Color Nombre")
    name_font = fields.Binary(string="Letra (Nombre)",attachment=True)
    name_font_filename = fields.Char()

    ###################  job configuration  ##############################
    x_job_position = fields.Integer(string="Posicion X (Puesto)", default=865)
    y_job_position = fields.Integer(string="Posicion Y (Puesto)", default=250)
    job_font_size = fields.Integer(string="Tamaño de letra (Puesto) ", default=30)
    job_color = fields.Char(default="#1B371F", string="Color Puesto")
    job_font = fields.Binary(string="Letra (Puesto)",attachment=True)
    job_font_filename = fields.Char()

    ###################  mobile configuration  ##############################
    x_mobile_position = fields.Integer(string="Posicion X (Telefono)", default=120)
    y_mobile_position = fields.Integer(string="Posicion Y (Telefono)", default=577)
    mobile_font_size = fields.Integer(string="Tamaño de letra (Telefono) ", default=30)
    mobile_color = fields.Char(default="#FFFFFF",string="Color Telefono")
    mobile_font = fields.Binary(string="Letra (Telefono)",attachment=True)
    mobile_font_filename = fields.Char()

    ###################  company phone configuration  ##############################
    x_phone_comp_position = fields.Integer(string="Posicion X (Empresa)", default=480)
    y_phone_comp_position = fields.Integer(string="Posicion Y (Empresa)", default=577)
    phone_comp_font_size = fields.Integer(string="Tamaño de letra (Empresa) ", default=30)
    company_color = fields.Char(default="#FFFFFF",string="Color Empresa")
    company_font = fields.Binary(string="Letra (Empresa)",attachment=True)
    company_font_filename = fields.Char()

    ###################  address configuration  ##############################
    x_address_position = fields.Integer(string="Posicion X (Direccion)", default=1160)
    y_address_position = fields.Integer(string="Posicion Y (Direccion)", default=577)
    address_font_size = fields.Integer(string="Tamaño de letra (Direccion) ", default=30)
    address_color = fields.Char(default="#FFFFFF",string="Color Direccion")
    address_font = fields.Binary(string="Letra (Direccion)",attachment=True)
    address_font_filename = fields.Char()