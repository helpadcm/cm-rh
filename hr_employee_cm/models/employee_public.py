from odoo import fields, models, api


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    branch_id = fields.Many2one(
        'hr.branch',
        related='employee_id.branch_id',
        string="Sucursal",
        help="Sucursal a la que pertenece el empleado."
        )

    employee_no = fields.Char(
        string="Código de Empleado",
        help="Este código es único para cada empleado y se utiliza para identificarlo en el sistema.",
        compute="_get_employee_no",
        compute_sudo=True
        )

    birthday_month = fields.Integer(string="Mes de nacimiento")

    # @api.depends('pin','barcode')
    # def _get_employee_no(self):
    #     for employee_public in self:
    #         employee_public.employee_no = employee_public.employee_id.employee_no
