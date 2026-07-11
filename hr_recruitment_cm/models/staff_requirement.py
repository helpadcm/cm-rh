# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from odoo.http import request

states = [
        ('draft','Borrador'),
        ('approval','Aprobacion'),
        ('in_progress','En Proceso'),
        ('finalized','Finalizado'),
        ('refused','Rechazado')
    ]

class staffRequirement(models.Model):
    _name = 'hr.staff.requirement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Modelo para requerimiento de personal'
    _order = 'date desc'

    @api.model
    def _get_user_actual(self):
        return self.env.user.id

    @api.model
    def _get_actual_date(self):
        return datetime.now().date()

    def _get_manager(self):
        resp_id = self.env['hr.employee'].search([('function_rrhh','=','rrhh_manager')])
        if resp_id:
            return resp_id.user_id.id

    @api.model
    def _get_number_default(self):
        try:
            sequence_id = self.env.ref('hr_recruitment_cm.req_staff_sequence')
            return sequence_id.get_next_char(sequence_id.number_next_actual)
        except:
            pass

    name = fields.Char(string="Nombre de Requerimiento",tracking=True,copy=False)
    aprobation_date = fields.Date(string="Fecha envio RRHH", tracking=True)
    number = fields.Char(string="Numero",default=_get_number_default,copy=False)
    department_id = fields.Many2one('hr.department',string="Area Solicitante",tracking=True,copy=False)
    job_id = fields.Many2one('hr.job',string="Puesto Solicitante",tracking=True,copy=False)
    rotation = fields.Boolean(string="Rotacion",tracking=True,copy=False)
    replate_to = fields.Char(string="Reemplaza a",tracking=True,copy=False)
    replace_job_id = fields.Many2one('hr.job',string="Puesto a Reemplazar",tracking=True,copy=False)
    city = fields.Many2one('res.city',string="Ciudad",tracking=True,copy=False)
    position_type = fields.Selection([('permanent','Permanente'),('temp','Temporal')],string="Tipo de plaza",tracking=True,copy=False)
    promotion = fields.Selection([('yes','SI'),('no','NO')],string="Promocion Interna",default="no",tracking=True,copy=False)
    promotion_name = fields.Many2one('hr.employee',string="Nombre de empleado",tracking=True,copy=False)
    state = fields.Selection(states,string="Estado",default="draft",tracking=True,copy=False)
    assigned_to = fields.Many2one('res.users',string="Asignado a",tracking=True,copy=False)
    manager_id = fields.Many2one('res.users',string="Responsable",default=_get_manager,tracking=True,copy=False)
    requested_by = fields.Many2one('res.users',string="Solicitado por",default=_get_user_actual,tracking=True,copy=False)
    date = fields.Date(string="Fecha de Solicitud",default=_get_actual_date, copy=False,tracking=True)
    new_position = fields.Many2one('hr.job',string="Nuevo Puesto",tracking=True,copy=False)
    postulation_id = fields.Many2one('hr.applicant',string="Postulacion", copy=False,tracking=True)
    postulation_created = fields.Boolean(string="Postulacion Creada", copy=False)
    requested_qty = fields.Integer(string="Cant. Solicitada",default=1)
    hired_qty = fields.Integer(string="Cant. Contratada")
    description = fields.Text(string="Motivo")
    salarial_range = fields.Float(string="Rango Salarial",tracking=True)
    follower_ids = fields.Many2many('res.users',string="Seguidores",tracking=True)

    @api.onchange('requested_by')
    def change_requested(self):
        if self.requested_by:
            employee_id = self.env['hr.employee'].search([('user_id','=',self.requested_by.id)])
            if employee_id:
                self.department_id = employee_id.department_id.id
                self.job_id = employee_id.job_id.id

    def change_state(self):
        state_type = self.env.context.get('state_type')
        if state_type:
            if state_type == 'approval':
                self.aprobation_date = (datetime.now() - timedelta(hours=6)).date()
                self.send_to_approve()
            self.state = state_type

    def send_to_approve(self):
        if self.manager_id.login:
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
            template_id = self.env.ref('hr_recruitment_cm.staff_request_requirement_template')
            template_ctx = {'action_url': base_url}
            template_id.with_context(**template_ctx).send_mail(self.id,force_send=True)

    def action_view_postulations(self):
        action = self.env["ir.actions.actions"]._for_xml_id("hr_recruitment.action_hr_job_applications")
        action['domain'] = [('requirement_id', '=', self.id)]
        action['context'] = {'create': False}
        return action

    @api.model_create_multi
    def create(self, vals):
        sequence_id = self.env.ref('hr_recruitment_cm.req_staff_sequence')
        res = super(staffRequirement, self).create(vals)
        sequence_id.next_by_id()
        return res

    def copy(self, default=None):
        self.env.context = dict(self.env.context)
        sequence_id = self.env.ref('hr_recruitment_cm.req_staff_sequence')
        next_number = sequence_id.get_next_char(sequence_id.number_next_actual)
        self.env.context.update({'number': next_number})
        res = super(staffRequirement, self).copy(default)
        return res

    def create_postulation(self):
        stage_id = self.env['hr.recruitment.stage'].search([('sequence','=',0)])
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Postulación',
            'res_model': 'hr.applicant',
            'view_mode': 'form',
            'context': {
                'default_requirement_id': self.id,
                'default_stage_id': stage_id.id,
                'default_department_id': self.department_id.id,
                'default_job_id': self.new_position.id,
                'default_user_id': self.env.user.id,
                'default_salary_proposed': self.salarial_range,
            },
            'target': 'new',
        }
        