import io
import zipfile
from datetime import timedelta
from itertools import groupby

import xlsxwriter

from odoo import api, fields, models


class HrAttendanceEmployeeReport(models.TransientModel):
    """
    Abstract class for Employee Attendance Report.
    """
    _name = "hr.attendance.employee.report"
    _description = "Employee Attendance Analysis Report Abstract"

    date = fields.Date('Date', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Employee')
    department_id = fields.Many2one('hr.department', 'Department', readonly=True, related='employee_id.department_id', )
    company_id = fields.Many2one('res.company', 'Company', readonly=True, related='employee_id.company_id')

    date_from = fields.Date('Start Date')
    date_to = fields.Date('End Date')

    apply_extra_hour = fields.Boolean('Have Extra Hour', compute='_compute_apply_extra_hour', readonly=True)

    total_hour = fields.Float('Total Hour', readonly=True)
    total_ordinary_hour = fields.Float('Total Ordinary Hour', readonly=True)
    total_extra_hour = fields.Float('Total Extra Hour', readonly=True)

    def _get_domain(self):
        return [
            ('check_in', '>=', self.date_from),
            ('check_in', '<=', self.date_to),
            ('employee_id', '=', self.employee_id.id),
            ]

    def _compute_apply_extra_hour(self):
        for record in self:
            if not record.employee_id.contract_id:
                record.apply_extra_hour = False
                return
            record.apply_extra_hour = record.employee_id.contract_id.work_entry_source != 'calendar'

    def _get_attendance(self):
        domain = self._get_domain()
        return self.env['hr.attendance'].search(domain).read()

    def groupby(self, iterable, key_func):
        result = []
        for item in iterable:
            key = key_func(item)
            if key not in result:
                result.append((key, []))
            result.append((key, item))
        return result

    def process_employee_attendance(self, employee, attendances):
        """
        Process the employee attendance data to be used in the reports.
        Only receive attendance from a single employee

        Parameters:
        attendances (list): The list of employee attendance data to be transformed.

        Returns:
        dict: The transformed data.
        """
        assert all(a.employee_id == employee.id for a in attendances)

        # Sort attendances by check_in date
        attendances.sort(key=lambda x: (x.check_in.date()))

        # Group attendances by employee_id and check_in date
        attendance_date = {
            _date: list(_attendance)
            for _date, _attendance in groupby(attendances, key=lambda x: x.check_in.date())
            }

        report = {"header": {}, "rows": []}

        start_date = attendances[0].check_in.date()
        end_date = attendances[-1].check_in.date()

        # a list of dates between start_date and end_date
        dates = (
            start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)
            )

        attendances_report = []

        for _date in dates:
            self._process_date(employee, _date, attendance_date)

        report["header"] = {
            "employee_id": employee.id,
            "employee_name": employee.name,
            "start_date": start_date,
            "end_date": end_date,
            "total_hours": sum(a["total_hours"] for a in attendances_report),
            "ordinary_hours": sum(a["ordinary_hours"] for a in attendances_report),
            "extra_hours": sum(a["extra_hours"] for a in attendances_report),
            }
        return report

    def _process_date(self, employee, _date, attendance_date):
        if _date not in attendance_date:
            return {
                "employee_id": employee.id,
                "date": _date,
                "check_in_1": "",
                "check_out_1": "",
                "check_in_2": "",
                "check_out_2": "",
                "total_hours": 0,
                "ordinary_hours": 0,
                "extra_hours": 0,
                "observation": "No attendance for this date.",
                "transport_bonus": 0,
                }
        attendances = attendance_date[_date]
        assert len(attendances) > 0, "There should be at least one attendance for the date."
        worked_hours, ordinary_hours, extra_hours = self._compute_hours(attendances)
        observations = []
        if len(attendances) > 2:
            observations.append("More than 2 attendances for this date.")
        return {
            "employee_id": employee.id,
            "date": _date,
            "check_in_1": attendances[0].check_in,
            "check_out_1": attendances[0].check_out,
            "check_in_2": attendances[1].check_in if len(attendances) > 1 else "",
            "check_out_2": attendances[1].check_out if len(attendances) > 1 else "",
            "total_hours": worked_hours,
            "ordinary_hours": ordinary_hours,
            "extra_hours": extra_hours,
            "observation": ", ".join(observations) if observations else "",
            }

    def _compute_hours(self, attendances, precision=0.5):
        """
        Compute the hours worked by an employee in a day.


        Parameters:
        attendances (list): The list of employee attendance data to be transformed.

        Returns:
        float: The total hours worked by the employee.
        """
        worked_hours = sum(att.worked_hours for att in attendances)
        ordinary_hours = round(min(worked_hours, 8) / precision) * precision
        extra_hours = round(max(worked_hours - ordinary_hours, 0) / precision) * precision
        return worked_hours, ordinary_hours, extra_hours


class HrAttendanceEmployeesReport(models.TransientModel):
    """
    Employee Attendance Report.
    Its purpose is to provide a report that shows the attendance of employees for a given period.
    Its decision to be used to calculate the total hours worked by an employee in a given period
    for the purpose of payroll and other analysis.
    """
    _name = "hr.attendance.employees.report"
    _description = "Employee Attendance Analysis Report"
    _rec_name = 'date'

    date = fields.Date('Date', readonly=True, default=fields.Date.context_today)
    department_id = fields.Many2one('hr.department', 'Department')
    employee_ids = fields.Many2many('hr.employee', 'Employee')
    company_id = fields.Many2one('res.company', 'Company', readonly=True)

    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)

    @api.onchange('department_id')
    def _get_users_by_department(self):
        """
        Get the employees of the selected department.
        """
        if self.department_id:
            self.employee_ids = self.env['hr.employee'].search(
                [('department_id', '=', self.department_id.id), ('contract_id', '!=', False)]
                )

    @staticmethod
    def _excel_formats(workbook):
        """
        Define the formats to be used in the Excel file.
    
        Parameters:
        workbook (xlsxwriter.Workbook): The workbook to be used.
    
        Returns:
        dict: The formats to be used in the Excel file.
        """
        date_format = workbook.add_format({"num_format": "yyyy-mm-dd"})
        header_format = workbook.add_format({"bold": True, "border": 1})
        body_format = workbook.add_format(
            {"border": 1, "font_name": "Arial", "align": "left"}
            )
        body_date_format = workbook.add_format(
            {
                "num_format": "yyyy-mm-dd",
                "border": 1,
                "font_name": "Arial",
                "align": "left",
                }
            )
        return {
            "date_format": date_format,
            "header_format": header_format,
            "body_format": body_format,
            "body_date_format": body_date_format,
            }

    @staticmethod
    def _process_excel_headers(
            data_header,
            worksheet,
            formats,
            ):
        """
        Process the headers of the report.
    
        Parameters:
        data_header (EmployeeAttendanceHeader): The list of employee data to be transformed.
        workbook (xlsxwriter.Workbook.worksheet_class): The workbook to be used.
    
        Returns:
        None
        """
        worksheet.write("A1", "Employee Name", formats["header_format"])
        worksheet.write("C1", "Start Date", formats["header_format"])
        worksheet.write("D1", "End Date", formats["header_format"])
        worksheet.write("E1", "Total Hours", formats["header_format"])
        worksheet.write("F1", "Ordinary Hours", formats["header_format"])
        worksheet.write("G1", "Extra Hours", formats["header_format"])
        worksheet.write("A2", data_header["employee_id"], formats["body_format"])
        worksheet.write("C2", data_header["start_date"], formats["body_date_format"])
        worksheet.write("D2", data_header["end_date"], formats["body_date_format"])
        worksheet.write("E2", data_header["total_hours"], formats["body_format"])
        worksheet.write("F2", data_header["ordinary_hours"], formats["body_format"])
        worksheet.write("G2", data_header["extra_hours"], formats["body_format"])

    @staticmethod
    def _process_excel_rows(
            data_rows,
            worksheet,
            formats,
            ):
        """
        Process the rows of the report.
    
        Parameters:
        data_rows (list): The list of employee data to be transformed.
        workbook (xlsxwriter.Workbook.worksheet_class): The workbook to be used.
    
        Returns:
        None
        """
        headers = [
            "Fecha",
            "Dia",
            "Turno 1 (Entrada)",
            "Turno 1 (Salida)",
            "Turno 1 (Horas totales)",
            "Turno 2 (Entrada)",
            "Turno 2 (Salida)",
            "Turno 2 (Horas totales)",
            "Horas totales",
            "Horas ordinarias",
            "Horas extras",
            ]
        header_format = formats["header_format"]
        body_format = formats["body_format"]
        body_date_format = formats["body_date_format"]

        # Write the headers to the worksheet with the new format and set the column width
        for i, header in enumerate(headers):
            worksheet.write(3, i, header, header_format)
            worksheet.set_column(i, i, len(header) + 2)

        # Write the rows to the worksheet with the new format
        row = 4
        for data_row in data_rows:
            worksheet.write(row, 0, data_row["date"], body_date_format)
            worksheet.write(row, 1, data_row["date"].strftime("%A"), body_format)
            for i, entry in enumerate(data_row["entries"]):
                if i > 1:
                    break
                worksheet.write(row, 2 + i * 3, entry["checkin"], body_format)
                worksheet.write(row, 3 + i * 3, entry["checkout"], body_format)
                worksheet.write(row, 4 + i * 3, entry["total_hours"], body_format)
            worksheet.write(row, 10, data_row["total_hours"], body_format)
            worksheet.write(row, 11, data_row["ordinary_hours"], body_format)
            worksheet.write(row, 12, data_row["extra_hours"], body_format)
            row += 1

    def export_to_excel(self):
        """
        Writes it to an Excel file.
        For each employee in the employes_data list, write the data to the output_path Excel file with the name of 
        the employee.+
        The header of the report.
        The header of the detail is the following: 'Fecha', 'Entrada', 'Salida', 'Horas totales', 'Horas extras', 
        'Horas ordinarias'.
        The rows of the report.
    
        Parameters:
        employes_data (list): The list of employee data to be transformed.
        output_path (str): The path to the output Excel file.
    
        Returns:
        None
        """
        self.ensure_one()

        employee_attendances = self._get_attendance()
        employee_attendance_data = self.process_employee_attendance(self.employee_id, employee_attendances)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(
            output, {
                'in_memory': True,
                'strings_to_formulas': False,
                }
            )
        formats = self._excel_formats(workbook)

        worksheet = workbook.add_worksheet()

        data_header = employee_attendance_data["header"]
        self._process_excel_headers(data_header, worksheet, formats)

        data_rows = employee_attendance_data["rows"]
        self._process_excel_rows(data_rows, worksheet, formats)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return {
            'file_name': f'Employee Attendance Report - {employee_attendance_data["header"]["employee_id"]}.xlsx',
            'file_content': generated_file,
            'file_type': 'xlsx',
            }

    def export_to_excel_for_multiple_employees(self):
        """
        Generates Excel reports for multiple employees and returns them as a ZIP file.

        Parameters:
        employee_ids (list): List of employee IDs for which to generate reports.

        Returns:
        dict: Information about the generated ZIP file containing all Excel reports.
        """
        self.ensure_one()

        # Create a ZIP file in memory
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for employee_id in self.employee_ids:
                employee_report = self.env['hr.attendance.employee.report'].create(
                    {
                        'employee_id': employee_id.id,
                        'date_from': self.date_from,
                        'date_to': self.date_to,
                        }
                    )

                # Utilizar los métodos del modelo abstracto para obtener y procesar los datos
                employee_attendances = employee_report._get_attendance()
                employee_attendance_data = employee_report.process_employee_attendance(
                    employee_report.employee_id, employee_attendances
                    )

                # Crear un archivo Excel en memoria para el empleado actual
                employee_output = io.BytesIO()
                workbook = xlsxwriter.Workbook(employee_output, {'in_memory': True})
                formats = self._excel_formats(workbook)
                worksheet = workbook.add_worksheet()

                data_header = employee_attendance_data["header"]
                self._process_excel_headers(data_header, worksheet, formats)

                data_rows = employee_attendance_data["rows"]
                self._process_excel_rows(data_rows, worksheet, formats)

                workbook.close()

                # Añadir el archivo Excel al archivo ZIP
                employee_name = self.env['hr.employee'].browse(employee_id).name
                zipf.writestr(f'Employee Attendance Report - {employee_name}.xlsx', employee_output.getvalue())

        output.seek(0)
        zip_content = output.read()
        output.close()

        return {
            'file_name': 'Employee Attendance Reports.zip',
            'file_content': zip_content,
            'file_type': 'zip',
            }
