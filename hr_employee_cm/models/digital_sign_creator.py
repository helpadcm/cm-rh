import base64
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
            self.job = self.employee_id.job_id.name
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
    x_name_position = fields.Integer(string="Posicion X (Nombre)", default=720)
    y_name_position = fields.Integer(string="Posicion Y (Nombre)", default=130)
    name_font_size = fields.Integer(string="Tamaño de letra (Nombre) ", default=70)

    ###################  job configuration  ##############################
    x_job_position = fields.Integer(string="Posicion X (Puesto)", default=720)
    y_job_position = fields.Integer(string="Posicion Y (Puesto)", default=210)
    job_font_size = fields.Integer(string="Tamaño de letra (Puesto) ", default=27)

    ###################  mobile configuration  ##############################
    x_mobile_position = fields.Integer(string="Posicion X (Telefono)", default=178)
    y_mobile_position = fields.Integer(string="Posicion Y (Telefono)", default=467)
    mobile_font_size = fields.Integer(string="Tamaño de letra (Telefono) ", default=27)

    ###################  address configuration  ##############################
    x_address_position = fields.Integer(string="Posicion X (Direccion)", default=965)
    y_address_position = fields.Integer(string="Posicion Y (Direccion)", default=467)
    address_font_size = fields.Integer(string="Tamaño de letra (Direccion) ", default=27)