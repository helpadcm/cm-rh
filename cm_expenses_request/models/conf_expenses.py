# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class confExpenses(models.Model):
    _name = 'conf.expenses.request'
    _description = "Configuracion gastos"

    name = fields.Char(string="Nombre")
    details_expenses_ids = fields.One2many('cm.expenses.conf.details','conf_id',string="Detalles de viaticos")
    job_ids = fields.Many2many('hr.job',string="Puestos de trabajo")

class expensesDetails(models.Model):
    _name = 'cm.expenses.conf.details'
    _description = "Detalles Solicitud de viaticos por puesto"

    conf_id = fields.Many2one('conf.expenses.request',string="Conf")
    ctis_ids = fields.Many2many('cargo.airport',string="Ciudad")
    breakfast_amount = fields.Float(string="Desayuno")
    lunch_amount = fields.Float(string="Almuerzo")
    dinner_amount = fields.Float(string="Cena")
    total_amount = fields.Float(string="Total")
    currency_id = fields.Many2one('res.currency',string="Moneda")

    @api.onchange('breakfast_amount','lunch_amount','dinner_amount')
    def get_total(self):
        self.total_amount = self.breakfast_amount + self.lunch_amount + self.dinner_amount