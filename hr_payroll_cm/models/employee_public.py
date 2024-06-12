from odoo import fields, models


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    employee_no = fields.Char(
        string="Código de Empleado",
        help="Este código es único para cada empleado y se utiliza para identificarlo en el sistema.",
        compute="_get_employee_no"
        )

    def _get_employee_no(self):
        for record in self:
            record.employee_no = record['registration_number'] or record['barcode'] or record['pin'] or ''
