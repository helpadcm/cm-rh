import io

import xlsxwriter

from odoo import models


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def _get_payslips_data(self):
        """
        Get the data from the payslips as 
        :return: 
        """

    def _get_payslips_by_structure(self):
        """
        Get the payslips grouped by structure
        :return: 
        """
        return self.slip_ids.mapped('struct_id')

    def _get_payslips_by_department(self):
        """
        Get the payslips grouped by department
        :return: 
        """
        return self.slip_ids.mapped('employee_id.department_id')

    def _get_payslips_as_tuple(self, payslip):
        """
        Get the payslip from the payslip class to payslip tuple for the report
        :return: PaySlipReport
        """
        pass

    def _get_payslips_grouped_by_department(self):
        """
        Get the payslips grouped by department
        :return: list of ReportGroup
        """
        pass

    def action_download_report(self):
        """
        Generate and download the payroll report in Excel format.
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Payroll Report')

        bold = workbook.add_format({'bold': True})

        worksheet.write('A1', 'Employee', bold)
        worksheet.write('B1', 'Wage', bold)
        worksheet.write('C1', 'Hours Worked', bold)
        worksheet.write('D1', 'Extra Hours', bold)
        worksheet.write('E1', 'Total Pay', bold)

        row = 1
        col = 0

        for payslip in self.slip_ids:
            worksheet.write(row, col, payslip.employee_id.name)
            worksheet.write(row, col + 1, payslip.contract_id.wage)
            worksheet.write(row, col + 2, payslip.worked_days_line_ids.mapped('number_of_hours'))
            worksheet.write(
                row, col + 3, payslip.input_line_ids.filtered(lambda l: l.code == 'OVERTIME125').mapped('amount')
                )
            worksheet.write(row, col + 4, payslip.amount_total)
            row += 1

        # Close the workbook before streaming the data.
        workbook.close()
        output.seek(0)
        xlsx_data = output.read()
        output.close()

        # Encode the Excel file in base64.
        encoded_data = base64.b64encode(xlsx_data)

        # Create an attachment.
        attachment = self.env['ir.attachment'].create(
            {
                'name': 'Payroll_Report.xlsx',
                'type': 'binary',
                'datas': encoded_data,
                'store_fname': 'Payroll_Report.xlsx',
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                }
            )

        # Return the action to download the file.
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
            }
