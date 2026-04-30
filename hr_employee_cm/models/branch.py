from odoo import fields, models


class Branch(models.Model):
    _name = 'hr.branch'
    _description = 'Branch'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    city_id = fields.Many2one('res.city', string='City', required=True)
    parent_id = fields.Many2one('hr.branch', string='Parent Branch')
    child_ids = fields.One2many('hr.branch', 'parent_id', string='Child Branches')
    manager_id = fields.Many2one('hr.employee', string='Manager')
    employee_ids = fields.One2many('hr.employee', 'branch_id', string='Employees')
    active = fields.Boolean('Active', default=True)
    color = fields.Integer('Color Index')
    exact_address = fields.Char(string="Direccion Exacta")

    _code_unique = models.Constraint('unique(code)', message='El codigo debe ser unico por sucursal!')