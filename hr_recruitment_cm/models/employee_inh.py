# -*- coding: utf-8 -*-
from odoo import api, fields, models

class employeeInh(models.Model):
    _inherit = 'hr.employee'

    rrhh_boss = fields.Boolean(string="Encargado RRHH")
    function_rrhh = fields.Selection([('rrhh_boss','Encargado RRHH'),('rrhh_manager','Responsable RRHH')],string="Puesto en RRHH")

class employeePublicInh(models.Model):
    _inherit = 'hr.employee.public'

    rrhh_boss = fields.Boolean(string="Encargado RRHH")
    function_rrhh = fields.Selection([('rrhh_boss','Encargado RRHH'),('rrhh_manager','Responsable RRHH')],string="Puesto en RRHH")

# class RecruitmentStageInh(models.Model):
#     _inherit = 'hr.recruitment.stage'

#     limit_time = fields.Char(string="Tiempo Limite")