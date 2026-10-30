# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class handlingDailySales(models.TransientModel):
    _name = "handling.daily_sales_agent"
    _description = "Reportes ventas diarias de agentes"

    @api.model
    def default_get(self, fields):
        rec = super(handlingDailySales, self).default_get(fields)
        user_id = self.env.user
        employee_ids = False
        if self.env.user.has_group("cm_cargo_handling.group_guia_cargar_admin"):
            employee_ids = self.env['hr.employee'].search([])
        else:
            employee_id = self.env['hr.employee'].search([('user_id','=',user_id.id)])
            employee_ids = self.env['hr.employee'].search([('parent_id','=',employee_id.id)])

        if employee_ids:
            rec.update({
                'allow_employee_ids': employee_ids
            })
        return rec

    start_date = fields.Date(string="Fecha Inicial")
    final_date = fields.Date(string="Fecha Final")
    employee_ids = fields.Many2many('hr.employee','my_employee_rel',string="Empleados")
    allow_employee_ids = fields.Many2many('hr.employee','allow_employee_rel',string="Empleados a cargo")

    def print_report(self):
        consult_employees_ids = self.employee_ids
        if not self.employee_ids:
            consult_employees_ids = self.allow_employee_ids

        data = {
            'start_date': self.start_date,
            'final_date': self.final_date,
            'employee_ids': consult_employees_ids.mapped('user_id').ids
        }
        return self.env.ref('cm_cargo_handling.action_daily_sales_agent_report').report_action(self,data=data)