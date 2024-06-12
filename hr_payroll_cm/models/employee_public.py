from odoo import fields, models


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    employee_no = fields.Char(
        string="Código de Empleado",
        help="Este código es único para cada empleado y se utiliza para identificarlo en el sistema.",
        compute="_get_employee_no"
        )

    def _get_employee_no(self):
        for employee_public in self:
            employee_public.employee_no = (employee_public.employee_id.registration_number or
                                           employee_public.employee_id.barcode or employee_public.employee_id.pin or '')
