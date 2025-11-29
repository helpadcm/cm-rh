# -*- coding: utf-8 -*-
from odoo.http import request
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime

class othersRequests(models.Model):    
    _name = 'rrhh.others.requests'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Otras Solicitudes"

    @api.model
    def _default_date(self):
        return datetime.now().date()

    @api.model
    def default_company(self):
        return self.env.user.company_id.id

        
    name = fields.Char(string="Numero",default="Nuevo",copy=False,tracking=True)
    employee_id = fields.Many2one('hr.employee',string="Empleado",tracking=True)
    date = fields.Date(string="Fecha de Solicitud",default=_default_date)
    initial_date = fields.Date(string="Fecha de Inicio",copy=False,tracking=True)
    exit_date = fields.Date(string="Fecha de Fin",copy=False,tracking=True)
    people_qty = fields.Integer(string="Num. Personas",copy=False,tracking=True)
    qty_available = fields.Char(string="Cantidad disponible")
    business_id = fields.Many2one('cm.business.list',string="Lugar",copy=False,tracking=True)
    state = fields.Selection([('draft','Borrador'),('to_approve','Por Aprobar'),('approved','Aprobado'),('refused','Rechazado')],string="Estado",default="draft",copy=False,tracking=True)
    business_type = fields.Selection([('hotel','Hotel'),('ferry','Ferry')],string="Tipo de negocio")
    beneficiary_ids = fields.One2many('request.beneficiary','request_id',string="Beneficiarios")
    observations = fields.Text(string="Observaciones",tracking=True)

    exit_route_id = fields.Many2one('cm.ferry.routes',string="Ruta de Salida", tracking=True)
    return_route_id = fields.Many2one('cm.ferry.routes',string="Ruta de Regreso", tracking=True)
    exit_only = fields.Boolean(string="Solo Salida",tracking=True)
    open_back = fields.Boolean(string="Regreso Abierto",tracking=True)
    attachment_ids = fields.Many2many('ir.attachment',string='Adjuntos',help='Archivos relacionados con la solicitud')
    char_date_from = fields.Char(string="Fecha inicial string")
    char_date_to = fields.Char(string="Fecha final string")
    company_id = fields.Many2one('res.company',string="Empresa",default=default_company)
    
    @api.onchange('employee_id')
    def get_qty_available(self):
        history_ids = self.search([('employee_id','=',self.employee_id.id),('business_type','=','ferry'),('state','=','approved')])

        actual_month = datetime.now().month
        month_requests = history_ids.filtered(lambda history: history.date.month == actual_month)

        if not month_requests:
            ferry_tickets = '4'
        else:
            qty_month_requests = sum(month_requests.mapped('people_qty'))
            if qty_month_requests >= 4:
                ferry_tickets = 'No Disponible'
            else:
                ferry_tickets = 4 - qty_month_requests
        self.qty_available = ferry_tickets

    @api.onchange('initial_date','exit_date')
    def get_name_date(self):
        if self.initial_date:
            name_date = self.convert_date(self.initial_date)
            self.char_date_from = name_date
        if self.exit_date:
            name_date = self.convert_date(self.exit_date)
            self.char_date_to = name_date

    @api.onchange('business_id')
    def change_business(self):
        if self.business_id:
            self.business_type = self.business_id.business_type

    def change_state(self):
        next_state = self.env.context.get('state')
        if next_state == 'to_approve':
            self.validate_to_approve()

            if self.name == 'Nuevo':
                sequence_id = self.env.ref('cm_rrhh_management.request_other_sequence')
                if sequence_id:
                    self.name = sequence_id.next_by_id()
                    
            employee_noti_id = self.env['hr.employee'].sudo().search([('notify_validate_turns','=',True)])
            if employee_noti_id:
                if self.business_type == 'hotel':
                    request_type = 'Cotizacion de Hotel'
                else:
                    request_type = 'Boletos en Ferry'

                mail = self.env['mail.mail'].sudo().create({
                    'subject': "Solicitud %s creada por %s"%(self.name, self.employee_id.name),
                    'body_html': f"""<p>Se ha creado la solicitud <strong>{self.name}</strong> para <strong>{request_type}</strong> para que pueda ser revisada</p>""",
                    'email_to': employee_noti_id.user_id.login,
                })
                mail.send()

        if next_state == 'approved':
            self.send_email(self.business_type)

        self.state = next_state

    def validate_to_approve(self):
        if self.business_type == 'ferry':
            if self.qty_available == 'No Disponible':
                raise ValidationError(f"""El empleado {self.employee_id.name} no tiene boletos disponible para el mes.""")

        if self.people_qty <= 0:
            raise ValidationError("La cantidad solicitada deber ser mayor de 0.")

        if self.people_qty == 0:
            raise ValidationError("Debe agregar al menos un beneficiario")
        
        if len(self.beneficiary_ids) != self.people_qty:
            raise ValidationError("Debe agregar el numero de beneficiarios que especifico en la solicitud")
        else:
            benef_list = self.beneficiary_ids.mapped('beneficiary_id').ids
            if len(benef_list) != self.people_qty:
                raise ValidationError("Los beneficiarios no pueden estar repetidos")

    def unlink(self):
        if self.state != 'draft':
            raise ValidationError("Solo puede borrar solicitudes en estado borrador")
        return super(othersRequests, self).unlink()

    def send_email(self, type_business):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        if type_business == 'hotel':
            template_id = self.env.ref('cm_rrhh_management.other_request_email_template')
        else:
            template_id = self.env.ref('cm_rrhh_management.ferry_request_email_template')
        template_ctx = {'action_url': base_url}
        template_id.attachment_ids = [(6, 0, self.attachment_ids.ids)]
        template_id.with_context(**template_ctx).sudo().send_mail(self.id, force_send=True)

    def convert_date(self, date):
        months = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")
        
        day = date.day
        month = months[date.month]
        year = date.year

        return f"{day} de {month} del {year}"


class beneficiryRequests(models.Model):    
    _name = 'request.beneficiary'
    _description = "Beneficiarios de Solicitud"

    request_id = fields.Many2one('rrhh.others.requests',string="Solicitud")
    employee_id = fields.Many2one('hr.employee',string="Empleado")
    beneficiary_id = fields.Many2one('beneficiaries.detail.list',string="Nombre")
    identity = fields.Char(string="Identidad", related="beneficiary_id.identity")
    birthday = fields.Date(string="Fecha de nacimiento", related="beneficiary_id.birthday")
    relationship = fields.Selection(string="Parentesto", related="beneficiary_id.relationship")
    observation = fields.Char(string="Observaciones", related="beneficiary_id.observation")