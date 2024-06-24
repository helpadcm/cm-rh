from odoo import models, fields, api


class Employee(models.Model):
    _inherit = 'hr.employee'

    seniority = fields.Text(
        string='Antigüedad',
        help='Calcula la antigüedad basado en la fecha de contrato',
        compute='_compute_seniority'
        )

    @api.depends('contract_id.date_start')
    def _compute_seniority(self):
        for employee in self:
            if employee.contract_id:
                seniority = fields.Date.today() - employee.contract_id.date_start
                employee.seniority = f'{seniority.year} años, {seniority.month} meses y {seniority.day} días'
            else:
                employee.seniority = False
