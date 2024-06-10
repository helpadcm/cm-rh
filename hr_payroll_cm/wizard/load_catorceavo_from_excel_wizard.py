import base64
import io
import json

import xlrd

from odoo import api, fields, models


class LoadCatorceavoFromExcelWizard(models.TransientModel):
    """
    Load a excel file containing the catorceavo information.
    """
    _name = 'load.catorceavo.from.excel.wizard'
    _description = 'Load Catorceavo From Excel Wizard'

    file = fields.Binary('File', required=True)
    sheet_index = fields.Integer(string='Sheet Index', required=True, default=0)
    row_header = fields.Integer(string='Row Header', required=True, default=0)
    row_start = fields.Integer(string='Row Start', required=True, default=1)
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Run')
    payslip_ids = fields.Many2many('hr.payslip', string='Payslips')
    warnings = fields.Text(string='Warnings')
    raw_payslips = fields.Text(string='Raw Payslips')

    def set_raw_payslips(self, raw_payslips):
        self.raw_payslips = raw_payslips

    def get_raw_payslips(self):
        return json.loads(self.raw_payslips)

    @api.model
    def default_get(self, fields_list):
        defaults = super(LoadCatorceavoFromExcelWizard, self).default_get(fields_list)
        defaults['payslip_run_id'] = self.env.context.get('active_id')
        return defaults

    def _find_payslips_by_id(self, raw_payslips):
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

    def _load_raw_payslip(self):
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
        # Deben de obtenerse los valores de horas extras, bonos de transporte,
        # bonos de alimentacion, bonos por resultado, bonos de alimentacion
        # ajuste salarial, comisiones, incapacidad
        raw_payslips = []
        map_row = {
            'id': 1,
            'monto_catorceavo': 4,
            'deducciones': 5,
            'total': 6,
            }
        for row_index in range(self.row_start, sheet.nrows):
            row = sheet.row_values(row_index)
            values = {key: row[value] for key, value in map_row.items()}
            raw_payslips.append(values)
        self._find_payslips_by_id(raw_payslips)
        self.set_raw_payslips(json.dumps(raw_payslips))

    def action_load_raw_payslip(self):
        self._load_raw_payslip()
        # Return a warning or a message when the payslips are loaded
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'load.catorceavo.from.excel.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
            }

    @staticmethod
    def safe_float_convert(str_value):
        try:
            return float(str_value)
        except ValueError:
            return None

    def action_process_payslips(self):
        raw_payslips = self.get_raw_payslips()
        for payslip in self.payslip_ids:
            raw_payslip = next((p for p in raw_payslips if p['id'] == payslip.employee_id.identification_id), None)
            if raw_payslip:
                lines = []
                payslip_values = {
                    'CTAVO': raw_payslip['monto_catorceavo'],
                    'ANTC14': raw_payslip['deducciones'],
                    'NET': raw_payslip['total'],
                    }
                for rule in sorted(payslip.struct_id.rule_ids, key=lambda x: x.sequence):
                    amount = self.safe_float_convert(payslip_values.get(rule.code))
                    if amount and amount > 0:
                        lines.append(
                            (0, 0, {
                                'name': rule.name,
                                'code': rule.code,
                                'sequence': rule.sequence,
                                'slip_id': payslip.id,
                                'amount': payslip_values.get(rule.code),
                                'contract_id': payslip.contract_id.id,
                                'salary_rule_id': rule.id,
                                'employee_id': payslip.employee_id.id,
                                'rate': 100.0,
                                'quantity': 1.0,
                                'total': payslip_values.get(rule.code),
                                })
                            )
                payslip.write({'line_ids': lines})
