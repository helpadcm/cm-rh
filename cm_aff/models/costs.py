# -*- coding: utf-8 -*-
from odoo import api, exceptions, models,fields, _
from datetime import datetime

selection_forms = [
    ('form01', 'Form 1'),
    ('form02', 'Form 2')
]

selection_period = [
    ('annual', 'Anual'),
    ('monthly', 'monthly'),
    ('useful_life', 'Vida Util')
]

class costs(models.Model):
    _name = 'aff.costs'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Rubros"

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Codigo")
    cost_type = fields.Selection([('fixed','Fijo'),('variable','Variable'),('leasing','Leasing')],string="Tipo de Rubro")
    description = fields.Char(string="Descripción")

    template_id = fields.Many2one('aff.cost.template', string='Plantilla de Parámetros')
    form_type = fields.Selection(selection_forms, string="Forms")
    period = fields.Selection(selection_period, string="Periodo-tipo")

    ################ FORM 1  ########################################
    form1_amount = fields.Float(string="Monto")

class trainingList(models.Model):
    _name = 'aff.trainings'
    _description = "Listados de capacitaciones"

    name = fields.Char(string="Nombre")
    apply_to = fields.Selection([('first_year','Primer Año'),('second_year','Segundo Año'),('both','Ambos')],string="Aplicar a")

class reservationsList(models.Model):
    _name = 'aff.reservations'
    _description = "Listados de reservas"

    name = fields.Char(string="Nombre")
    calculate_type = fields.Selection([('cycles','Ciclos'),('hours','Horas voladas'),('fixed','Fijo')],string="Tipo de calculo")
    penalty_applies = fields.Boolean(string="Aplica Penalidad")

class suppliesList(models.Model):
    _name = 'aff.supplies'
    _description = "Listados de suministros y lubricantes"

    name = fields.Char(string="Nombre")
    amount = fields.Float(string="Precio")

class supplierList(models.Model):
    _name = 'aff.suppliers'
    _description = "Listados de proveedores"

    name = fields.Char(string="Nombre")