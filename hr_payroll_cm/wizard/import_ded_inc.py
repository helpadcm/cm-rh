from odoo import models, fields, _, api
from babel.dates import format_date
import calendar
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from openpyxl import load_workbook
import base64
from io import BytesIO

class importIncomesDeductions(models.TransientModel):
    _name = "import.dedutions.incomes"
    _description = "Importar ingresos y deduducciones"

    @api.model
    def _get_default_note(self):
        message = """Los nombres de los empleados, tipos de deduccion e ingresos deben ser igual que los existentes en el sistema."""
        return message

    options = fields.Selection([('incomes','Ingresos'),('deductions','Deducciones')],string="Opcion",default="deductions")
    format_doc = fields.Binary(string="Formato de importacion")
    doc_name = fields.Char(string="Nombre de Documento")
    note = fields.Text(string="Nota", default=_get_default_note)

    def import_document(self):
        file_content = base64.b64decode(self.format_doc)

        wb = load_workbook(filename=BytesIO(file_content))
        ws = wb.active  # toma la primera hoja

        # Iterar por filas
        for row in ws.iter_rows(min_row=2, values_only=True):  # min_row=2 para saltar encabezados
            employee_name, description, ded_type, initial_date, final_date, monthly_amount, amount_total, fees = row

            employee_id = False
            type_id = False
            fees_values = False
            fees_qty = 0

            if not employee_name:
                raise ValidationError("Debe agregar nombre del empleado")
            else:
                employee_id = self.env['hr.employee'].search([('name','=',employee_name)])
                if not employee_id:
                    raise ValidationError(f"""No existe empleado con el nombre {employee_name}""")

            if not ded_type:
                raise ValidationError("Debe agregar el tipo de deduccion o ingreso")
            else:
                if self.options == 'deductions':
                    type_id = self.env['hr.salary.attachment.type'].search([('name','=',ded_type)])
                    if not type_id:
                        raise ValidationError(f"""No existe tipo de deduccion con el nombre {ded_type}""")
                else:
                    type_id = self.env['hr.payslip.input.type'].search([('name','=',ded_type)])
                    if not type_id:
                        raise ValidationError(f"""No existe tipo de ingreso con el nombre {ded_type}""")

            if not initial_date:
                raise ValidationError("Debe agregar la fecha de inicio")

            if not description:
                description = type_id.name

            if self.options == 'deduction':
                if not monthly_amount or monthly_amount <= 0:
                    raise ValidationError("Debe ingresar el monto mensual o debe ser mayor que 0")

            if not amount_total or amount_total <= 0:
                raise ValidationError("Debe ingresar el monto total o debe ser mayor que 0")

            if fees:
                fees_values = True
                fees_qty = fees

            if self.options == 'deductions':
                values = {
                    'employee_ids': [(4, employee_id.id)],
                    'deduction_type_id': type_id.id,
                    'description': description,
                    'date_start': initial_date,
                    'monthly_amount': monthly_amount,
                    'total_amount': amount_total,
                    'by_quotes': fees_values,
                    'quotes_number': fees_qty
                }

                deduction_id = self.env['hr.salary.attachment'].create(values)

                if fees_values:
                    deduction_id.create_plan()
            else:
                if not final_date:
                    raise ValidationError("Debe agregar la fecha de finalizacion")

                values = {
                    'employee_id': employee_id.id,
                    'input_type_id': type_id.id,
                    'name': description,
                    'start_date': initial_date,
                    'end_date': final_date,
                    'amount': amount_total,
                    'state': 'in_progress',
                    'by_quotes': fees_values,
                    'quotes_number': fees_qty
                }

                income_id = self.env['hr.other.incomes'].create(values)

                if fees_values:
                    income_id.create_plan()