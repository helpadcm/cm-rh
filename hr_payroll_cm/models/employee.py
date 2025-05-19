from odoo import models, fields, api


class Employee(models.Model):
    _inherit = 'hr.employee'

    def get_employee_no(self):
        for employee in self:
            employee.employee_no = employee.registration_number or employee.barcode or employee.pin or ''

class departmentInherit(models.Model):
    _inherit = 'hr.department'

    calculate_hours = fields.Selection([('one','1 vez'),('two','2 veces')], string="Calculo Horas al Mes", default="two")

class salaryRulesInh(models.Model):
    _inherit = 'hr.salary.rule'

    @api.model_create_multi
    def create(self, vals_list):
        rules = super().create(vals_list)
        self.env['hr.inc.ded.rules'].create({
            'name': rules.name,
            'code': rules.code,
            'category_id': rules.category_id.id
        })
        return rules