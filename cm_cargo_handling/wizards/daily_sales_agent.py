# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class handlingDailySales(models.TransientModel):
    _name = "handling.daily_sales_agent"
    _description = "Reportes ventas diarias de agentes"

    date = fields.Date(string="Fecha")
    employee_ids = fields.Many2many('hr.employee',string="Empleados")
    # allow_employee_ids = fields.Many2many('hr.employee',string="Empleados")    

    def print_report(self):
        data = {
            'date': self.date,
            'employee_ids': self.employee_ids.ids
        }
        return self.env.ref('cm_cargo_handling.action_daily_sales_report').report_action(self,data=data)