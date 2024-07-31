import base64
import io
import json

import xlrd

from odoo import api, fields, models


class LoadNominaFromExcelWizard(models.TransientModel):
    """
    Load a excel file,
    read the content,
    validate the content,
    and create the payroll
    """
    _name = 'load.nomina.from.excel.wizard'
    _description = 'Load Nomina From Excel Wizard'

    file = fields.Binary(string='File', required=True, )
    sheet_index = fields.Integer(string='Sheet Index', required=True, default=1)
    row_header = fields.Integer(string='Row Header', required=True, default=4)
    row_start = fields.Integer(string='Row Start', required=True, default=5)
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Run')
    payslip_ids = fields.Many2many('hr.payslip', string='Payslips')
    warnings = fields.Text(string='Warnings')
    total_ordinary_hours = fields.Float(string='Total Ordinary Hours', default=96)
    raw_payslips = fields.Text(string='Raw Payslips')

    def set_raw_payslips(self, raw_payslips):
        self.raw_payslips = raw_payslips

    def get_raw_payslips(self):
        return json.loads(self.raw_payslips)

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'payslip_run_id' in self.env.context:
            defaults['payslip_run_id'] = self.env.context['default_payslip_run_id']
        return defaults

    def action_load_raw_payslip(self):
        """
        Load the excel file
        """
        # Decode the base64 file content
        file_data = base64.b64decode(self.file)

        # Create a file-like object from the decoded content
        file_stream = io.BytesIO(file_data)

        # Open the workbook
        workbook = xlrd.open_workbook(file_contents=file_stream.read())
        sheet = workbook.sheet_by_index(self.sheet_index)
        headers = sheet.row_values(self.row_header)
        # Deben de obtenerse los valores de horas extras, bonos de transporte,
        # bonos de alimentacion, bonos por resultado, bonos de alimentacion
        # ajuste salarial, comisiones, incapacidad
        raw_payslips = []
        map_rows = {
            'id': 2,
            'hora_extra_25': 8,
            'monto_extra_25': 9,
            'hora_extra_50': 10,
            'monto_extra_50': 11,
            'feriado_trabajado': 12,
            'bono_transporte/alimentacion': 13,
            'comisiones': 14,
            'bono_resultado': 15,
            'ajuste_salarial': 16,
            'rap': 22,
            'cuentas_por_cobrar': 26,
            'incapacidad': 32,
            }
        for row_index in range(self.row_start, sheet.nrows):
            row = sheet.row_values(row_index)
            values = {key: row[value] for key, value in map_rows.items()}
            raw_payslips.append(values)
        self.find_payslips_by_id(raw_payslips)
        self.set_raw_payslips(json.dumps(raw_payslips))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'load.nomina.from.excel.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            }

    def find_payslips_by_id(self, raw_payslips):
        """
        Find a payslip by id
        """
        dnis = [payslip['id'] for payslip in raw_payslips if payslip['id'] != '']
        self.payslip_ids = self.env['hr.payslip'].search([('payslip_run_id', '=', self.payslip_run_id.id)])
        dnis_odoo = self.payslip_ids.mapped('employee_id.identification_id')
        dnis_not_found = [dni for dni in set(dnis + dnis_odoo) if dni not in dnis_odoo or dni not in dnis]
        warnings = []
        for dni in dnis_not_found:
            warnings.append(f'DNI {dni} not found')
        if warnings:
            self.warnings = '\n'.join(warnings)

    def action_process_payslips(self):
        """
        Process the payslips
        """
        raw_payslips = self.get_raw_payslips()
        for payslip in self.payslip_ids:
            raw_payslip = next(
                filter(
                    lambda r_payslip, ps = payslip: r_payslip['id'] == ps.employee_id.identification_id,
                    raw_payslips
                    ),
                None
                )
            if not raw_payslip:
                continue
            self.process_work_lines(payslip, raw_payslip)
            self.process_input_lines(payslip, raw_payslip)
            payslip.compute_sheet()

    def process_work_lines(self, payslip, payslip_raw):
        work_entry_type = self.env['hr.work.entry.type']
        ordynary_hours_type = work_entry_type.search([('code', '=', 'WORK100')])[0]
        extra_hours_25_type = work_entry_type.search([('code', '=', 'OVERTIME125')])[0]
        extra_hours_50_type = work_entry_type.search([('code', '=', 'OVERTIME150')])[0]
        # process_work_day_lines
        work_day_lines = []
        if payslip_raw['hora_extra_25'] and payslip_raw['hora_extra_25'] > 0:
            work_day_lines.append(
                {
                    'payslip_id': payslip.id,
                    'work_entry_type_id': extra_hours_25_type.id,
                    'amount': payslip_raw['monto_extra_25'],
                    'name': 'Horas Extras 25%',
                    'number_of_days': payslip_raw['hora_extra_25'] / 8,
                    'number_of_hours': payslip_raw['hora_extra_25']
                    }
                )
        if payslip_raw['hora_extra_50'] and payslip_raw['hora_extra_50'] > 0:
            work_day_lines.append(
                {
                    'payslip_id': payslip.id,
                    'work_entry_type_id': extra_hours_50_type.id,
                    'amount': payslip_raw['monto_extra_50'],
                    'name': 'Horas Extras 50%',
                    'number_of_days': payslip_raw['hora_extra_50'] / 8,
                    'number_of_hours': payslip_raw['hora_extra_50']
                    }
                )
        # process_bonos y deducciones:
        if len(work_day_lines) > 0:
            work_day_lines.append(
                {
                    'payslip_id': payslip.id,
                    'work_entry_type_id': ordynary_hours_type.id,
                    'amount': payslip.contract_id.wage,
                    'name': 'Tiempo Nominal',
                    'number_of_days': self.total_ordinary_hours / 8,
                    'number_of_hours': self.total_ordinary_hours
                    }
                )
            payslip.worked_days_line_ids.unlink()
            payslip.write({'edited': True})
            self.env['hr.payslip.worked_days'].create(work_day_lines)

    def process_input_lines(self, payslip, payslip_raw):
        input_lines = []
        if self._exist_and_gt0(payslip_raw['bono_transporte/alimentacion']):
            input_lines.append(
                {
                    "name": "Bonos de Transporte",
                    "code": "TRANSBONUS",
                    "amount": payslip_raw['bono_transporte/alimentacion'],
                    "contract_id": payslip.contract_id.id,
                    "payslip_id": payslip.id,
                    "input_type_id": payslip.env['hr.payslip.input.type'].search([("code", "=", "TRANSBONUS")])[
                        0].id,
                    }
                )
        if payslip_raw['feriado_trabajado'] and payslip_raw['feriado_trabajado'] > 0:
            input_lines.append(
                {
                    "name": "Feriado Trabajado",
                    "code": "REIMBURSEMENT",
                    "amount": payslip_raw['feriado_trabajado'],
                    "contract_id": payslip.contract_id.id,
                    "payslip_id": payslip.id,
                    "input_type_id": payslip.env['hr.payslip.input.type'].search([("code", "=", "REIMBURSEMENT")])[
                        0].id,
                    }
                )
        if self._exist_and_gt0(payslip_raw['comisiones']):
            input_lines.append(
                {
                    "name": "Comisiones",
                    "code": "REIMBURSEMENT",
                    "amount": payslip_raw['comisiones'],
                    "contract_id": payslip.contract_id.id,
                    "payslip_id": payslip.id,
                    "input_type_id": payslip.env['hr.payslip.input.type'].search([("code", "=", "REIMBURSEMENT")])[
                        0].id,
                    }
                )
        if self._exist_and_gt0(payslip_raw['bono_resultado']):
            input_lines.append(
                {
                    "name": "Bono por Resultado",
                    "code": "REIMBURSEMENT",
                    "amount": payslip_raw['bono_resultado'],
                    "contract_id": payslip.contract_id.id,
                    "payslip_id": payslip.id,
                    "input_type_id": payslip.env['hr.payslip.input.type'].search([("code", "=", "REIMBURSEMENT")])[
                        0].id,
                    }
                )
        if self._exist_and_gt0(payslip_raw['ajuste_salarial']):
            input_lines.append(
                {
                    "name": "Ajuste Salarial",
                    "code": "REIMBURSEMENT",
                    "amount": payslip_raw['ajuste_salarial'],
                    "contract_id": payslip.contract_id.id,
                    "payslip_id": payslip.id,
                    "input_type_id": payslip.env['hr.payslip.input.type'].search([("code", "=", "REIMBURSEMENT")])[
                        0].id,
                    }
                )
        if self._exist_and_gt0(payslip_raw['rap']):
            input_lines.append(
                {
                    "name": "RAP",
                    "code": "RAP",
                    "amount": payslip_raw['rap'],
                    "contract_id": payslip.contract_id.id,
                    "payslip_id": payslip.id,
                    "input_type_id": payslip.env['hr.payslip.input.type'].search([("code", "=", "RAP")])[
                        0].id,
                    }
                )
        if self._exist_and_gt0(payslip_raw['cuentas_por_cobrar']):
            input_lines.append(
                {
                    "name": "Cuentas por Cobrar",
                    "code": "CXC",
                    "amount": payslip_raw['cuentas_por_cobrar'],
                    "contract_id": payslip.contract_id.id,
                    "payslip_id": payslip.id,
                    "input_type_id": payslip.env['hr.payslip.input.type'].search([("code", "=", "CXC")])[
                        0].id,
                    }
                )
        if self._exist_and_gt0(payslip_raw['incapacidad']):
            input_lines.append(
                {
                    "name": "Incapacidad",
                    "code": "DEDUCTION",
                    "amount": payslip_raw['incapacidad'],
                    "contract_id": payslip.contract_id.id,
                    "payslip_id": payslip.id,
                    "input_type_id": payslip.env['hr.payslip.input.type'].search([("code", "=", "DEDUCTION")])[
                        0].id,
                    }
                )
        if input_lines:
            payslip.write({'edited': True})
            for transbonus_input_line in payslip.input_line_ids.filtered(
                    lambda
                            input_line: input_line.input_type_id.code == 'TRANSBONUS'
                    ):
                transbonus_input_line.unlink()
            self.env['hr.payslip.input'].create(input_lines)

    @staticmethod
    def _exist_and_gt0(value):
        return value and value > 0
