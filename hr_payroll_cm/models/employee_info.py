from odoo import api, fields, models


class HrEmployeeInfo(models.Model):
    _inherit = 'hr.employee'

    employee_no = fields.Char(string="Codigo de Empleado",
                              help="Este código es único para cada empleado y se utiliza para identificarlo en el sistema.",
                              compute="get_empoyee_no")

    def get_empoyee_no(self):
        for record in self:
            record.employee_no = record['registration_number'] or record['barcode'] or record['pin'] or ''
