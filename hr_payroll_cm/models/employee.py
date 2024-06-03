from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_no = fields.Char(
        string="Código de Empleado",
        help="Este código es único para cada empleado y se utiliza para identificarlo en el sistema.",
        compute="get_employee_no"
        )

    def get_employee_no(self):
        for record in self:
            record.employee_no = record['registration_number'] or record['barcode'] or record['pin'] or ''
