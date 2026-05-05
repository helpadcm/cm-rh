# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.http import request
from datetime import datetime

marital = [
    ('single', 'Soltero(a)'), ('married','Casado(a)'),
    ('free_union', 'Union Libre'), ('widower','Viudo(a)')
]

situation_select = [
    ('1', 'No tengo cuenta ni relacion'), ('2','Tengo una cuenta de ahorro'),
    ('3', 'Tengo una cuenta de cheques'), ('4','Tengo un credito activo'),
    ('5', 'Estoy en proceso de abrir una cuenta'), ('6','Tengo mora o situacion irregular')
]

class HrApplicantInh(models.Model):
    _inherit = 'hr.applicant'

    identity = fields.Char(string="Identidad")
    immediate_availability = fields.Boolean(string="Disponibilidad Inmediata")
    birthday = fields.Date(string="Fecha de Nacimiento")
    age = fields.Integer(string="Edad")
    negotiable = fields.Boolean(string="Negociable")
    marital_status = fields.Selection(marital, string="Estado Civil")
    children = fields.Text(string="Hijos, Genero y Edad")
    academic_level = fields.Selection([('1','Primaria Completa'),('2','Secundaria Completa'),('3','Diversificado'),('4','Pregrado'),('5','Postgrado')],string="Nivel Academico")
    last_institute = fields.Char(string="Institucion")
    graduation_year = fields.Char(string="Año de Graduacion")
    career_name = fields.Char(string="Nombre de la carrera")
    currently_studying = fields.Boolean(string="Estudia Actualmente")
    current_institute = fields.Char(string="En que Institucion")
    career_promedy = fields.Char(string="Carrera y Promedio")
    own_vehicle = fields.Selection([('car','Carro'),('motorcycle','Moto'),('no','Ninguno')],string="Vehiculo Propio")
    has_with = fields.Selection([('own_house','Casa Propia'),('rent','Alquila')],string="Cuenta con")
    availability_travel = fields.Boolean(string="Disponibilidad para Viajar")
    excel_level = fields.Selection([('low','Bajo'),('medium','Medio'),('high','Alto')],string="Nivel de Excel")
    english_level = fields.Selection([('low','Bajo'),('medium','Medio'),('high','Alto')],string="Nivel de Ingles")
    banpais_relation = fields.Boolean(string="Relacion BANPAIS")
    vigent_licence = fields.Boolean(string="Licencia Vigente")
    address = fields.Char(string="Direccion")
    city = fields.Char(string="Ciudad")

    laboral_history_ids = fields.One2many('applicant.laboral.history','applicant_id',string="Historial Academico")
    unemployed = fields.Text(string="Sin Empleo")
    expectatives = fields.Text(string="Expectativas CM")
    experience = fields.Text(string="Experencia en otras areas")
    knowledge_position = fields.Text(string="Conocimiento en el puesto")
    personal_experience = fields.Text(string="Experiencia en el manejo de personal")

    banpais_situation = fields.Selection(situation_select, string="Sitacion con banpais")
    disease = fields.Boolean(string="Ha padecido alguna enfermedad?")
    other_responsabilities = fields.Text(string="Otras responsabilidades")
    free_time = fields.Text(string="Tiempo libre")
    with_life = fields.Text(string="Con quien vive")
    plans = fields.Text(string="Planes")

    relations_ids = fields.One2many('applicant.relation.collaborator','applicant_id',string="Relaciones Colaboradores")
    laboral_reference_ids = fields.One2many('applicant.laboral.reference','applicant_id',string="Referencias Laborales")
    personal_reference_ids = fields.One2many('applicant.personal.reference','applicant_id',string="Referencias Personales")

    salary_proposed_extra = fields.Char("Proposed Salary Extra", help="Salary Proposed by the Organisation, extra advantages", tracking=True,groups=False)
    salary_expected_extra = fields.Char("Expected Salary Extra", help="Salary Expected by Applicant, extra advantages", tracking=True,groups=False)
    salary_proposed = fields.Float("Proposed Salary", aggregator="avg", help="Salary Proposed by the Organisation", tracking=True,groups=False)
    salary_expected = fields.Float("Expected Salary", aggregator="avg", help="Salary Expected by Applicant", tracking=True,groups=False)

    @api.model
    def default_get(self, fields_list):
        res = super(HrApplicantInh, self).default_get(fields_list)
        job_id = res.get('job_id')
        progress_requirement_id = self.env['hr.staff.requirement'].search([('new_position','=',job_id),('state','=','in_progress')])
        if progress_requirement_id and len(progress_requirement_id) == 1:
            res.update({'requirement_id': progress_requirement_id.id})
        return res

    requirement_id = fields.Many2one('hr.staff.requirement',string="Requerimiento")

    @api.onchange('stage_id')
    def update_hired_persons(self):
        if self.requirement_id and self.stage_id.hired_stage:
            self.requirement_id.hired_qty += 1
            if self.requirement_id.hired_qty == self.requirement_id.requested_qty:
                self.requirement_id.state = 'finalized'

    @api.onchange('birthday')
    def calculate_age(self):
        if self.birthday:
            self.age = (datetime.now().year - self.birthday.year)

    def _get_employee_create_vals(self):
        res = super(HrApplicantInh, self)._get_employee_create_vals()
        marital = 'other'
        if self.marital_status == 'single':
            marital = 'single'
        elif self.marital_status == 'married':
            marital = 'married'
        elif self.marital_status == 'free_union':
            marital = 'cohabitant'
        elif self.marital_status == 'widower':
            marital = 'widower'

        res.update({
            'name': self.partner_name.upper() or self.partner_id.display_name.upper(),
            'private_street': self.address,
            'private_city': self.city,
            'identification_id': self.identity,
            'birthday': self.birthday,
            'study_field': self.career_name,
            'study_school': self.last_institute,
            'marital': marital
        })
        return res

class laboralHistory(models.Model):
    _name = 'applicant.laboral.history'
    _description = "Historial Academico"

    applicant_id = fields.Many2one('hr.applicant',string="Aplicante")
    company_name = fields.Char(string="Empresa")
    position_name = fields.Char(string="Puesto que desempeño")
    time_worked = fields.Char(string="Tiempo Laborado")
    salary = fields.Float(string="Salario")
    reason = fields.Text(string="Razon de Abandono")
    functions = fields.Text(string="Funciones que desempeño")
    tastes = fields.Text(string="Que le gusto")
    no_tastes = fields.Text(string="Que no le gusto")

class relationCollaborator(models.Model):
    _name = 'applicant.relation.collaborator'
    _description = "Relacion colaboradores"

    applicant_id = fields.Many2one('hr.applicant',string="Aplicante")
    name = fields.Char(string="Nombre")
    relationship = fields.Char(string="Parentesco")
    currently_work = fields.Boolean(string="Trabaja Actualmente")
    branch = fields.Char(string="Sucursal")
    department = fields.Text(string="Departamento/Area")

class laboralReference(models.Model):
    _name = 'applicant.laboral.reference'
    _description = "Referencias Laborales"

    applicant_id = fields.Many2one('hr.applicant',string="Aplicante")
    name = fields.Char(string="Nombre")
    company = fields.Char(string="Empresa")
    position = fields.Char(string="Puesto")
    phone = fields.Char(string="Numero de telefono")

class personalReference(models.Model):
    _name = 'applicant.personal.reference'
    _description = "Referencias personales"

    applicant_id = fields.Many2one('hr.applicant',string="Aplicante")
    name = fields.Char(string="Nombre")
    relationship = fields.Char(string="Parentesco")
    phone = fields.Char(string="Numero de telefono")
    company = fields.Char(string="Empresa")