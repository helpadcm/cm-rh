# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError

hours_array = [
        ('0', '12:00 AM'), ('0.5', '12:30 AM'),('1', '1:00 AM'), ('1.5', '1:30 AM'),
        ('2', '2:00 AM'), ('2.5', '2:30 AM'),('3', '3:00 AM'), ('3.5', '3:30 AM'),
        ('4', '4:00 AM'), ('4.5', '4:30 AM'),('5', '5:00 AM'), ('5.5', '5:30 AM'),
        ('6', '6:00 AM'), ('6.5', '6:30 AM'),('7', '7:00 AM'), ('7.5', '7:30 AM'),
        ('8', '8:00 AM'), ('8.5', '8:30 AM'),('9', '9:00 AM'), ('9.5', '9:30 AM'),
        ('10', '10:00 AM'), ('10.5', '10:30 AM'),('11', '11:00 AM'), ('11.5', '11:30 AM'),
        ('12', '12:00 PM'), ('12.5', '12:30 PM'),('13', '1:00 PM'), ('13.5', '1:30 PM'),
        ('14', '2:00 PM'), ('14.5', '2:30 PM'),('15', '3:00 PM'), ('15.5', '3:30 PM'),
        ('16', '4:00 PM'), ('16.5', '4:30 PM'),('17', '5:00 PM'), ('17.5', '5:30 PM'),
        ('18', '6:00 PM'), ('18.5', '6:30 PM'),('19', '7:00 PM'), ('19.5', '7:30 PM'),
        ('20', '8:00 PM'), ('20.5', '8:30 PM'),('21', '9:00 PM'), ('21.5', '9:30 PM'),
        ('22', '10:00 PM'), ('22.5', '10:30 PM'),('23', '11:00 PM'), ('23.5', '11:30 PM')] 

class TrainingsRRHH(models.Model):    
    _name = 'cm.rrhh.trainings'
    _description = "Control de capacitaciones"
    _inherit = ['mail.thread','mail.activity.mixin']

    @api.model
    def default_company(self):
        return self.env.user.company_id.id

    name = fields.Char(string="Nombre", tracking=True)
    date = fields.Date(string="Fecha", tracking=True)
    external_instructor = fields.Boolean(string="Instructor Externo")
    instructor = fields.Char(string="Instructor", tracking=True)
    instructor_ids = fields.Many2many('hr.employee',string="Instructores")
    place = fields.Char(string="Lugar", tracking=True)
    initial_hour = fields.Selection(hours_array,string="Hora de Inicio", tracking=True)
    final_hour = fields.Selection(hours_array, string="Hora Final", tracking=True)
    participants_ids = fields.One2many('cm.rrhh.trainings.shares', 'training_id', string="Participantes", tracking=True)
    company_id = fields.Many2one('res.company',string="Empresa",default=default_company)

class TrainingsShares(models.Model):    
    _name = 'cm.rrhh.trainings.shares'
    _description = "Participaciones de capacitaciones"

    employee_id = fields.Many2one('hr.employee',string="Empleado")
    certificate_delivered = fields.Boolean(string="Certificado entregado", copy=False)
    certificate_file = fields.Binary(string="Certificado", copy=False)
    certificate_file_name = fields.Char(string="Nombre Certificado", copy=False)
    training_id = fields.Many2one('cm.rrhh.trainings',string="Capacitacion")