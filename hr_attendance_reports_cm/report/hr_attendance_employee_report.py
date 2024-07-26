import base64
import io
import zipfile
from datetime import timedelta, time
from itertools import groupby

import xlsxwriter
from babel.dates import format_date
from pytz import timezone

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


def convert_to_user_tz(datetime_field, user_tz):
    if datetime_field:
        # Assuming the server stores datetime in UTC
        utc_tz = timezone('UTC')
        user_timezone = timezone(user_tz)

        # Convert the naive datetime to "aware" datetime in UTC
        datetime_field_utc = utc_tz.localize(fields.Datetime.from_string(datetime_field))

        # Convert to the user's timezone
        datetime_field_user_tz = datetime_field_utc.astimezone(user_timezone)

        return datetime_field_user_tz
    return ""


def float_to_time(float_hour):
    """
    Convert a float hour representation to a time object.

    Parameters:
    float_hour (float): The hour in float format, where the decimal part represents minutes.

    Returns:
    datetime.time: The time object.
    """
    hours = int(float_hour)
    minutes = int((float_hour - hours) * 60)
    if not 0 <= minutes < 60:
        raise ValueError("Minutos deben estar entre 0 y 59.")
    if not 0 <= hours < 24:
        raise ValueError("Las horas deben estar entre 0 y 23.")
    return time(hours, minutes)


def compare_datetime_with_float(datetime_obj, float_hour, operator):
    """
    Compare a datetime object with a float representing a time.

    Parameters:
    datetime_obj (datetime): The datetime object to compare.
    float_hour (float): The float representing a time to compare against.

    Returns:
    bool: True if the time part of datetime_obj is less than the time represented by float_hour, False otherwise.
    """
    time_obj = float_to_time(float_hour)

    if operator == '<':
        return datetime_obj.time() < time_obj
    elif operator == '>':
        return datetime_obj.time() > time_obj


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

    def get_attendance(self):
        domain = self._get_domain()
        return self.env['hr.attendance'].search(domain)

    def groupby(self, iterable, key_func):
        result = []
        for item in iterable:
            key = key_func(item)
            if key not in result:
                result.append((key, []))
            result.append((key, item))
        return result

    def process_employee_attendance(self):
        """
        Process the employee attendance data to be used in the reports.
        Only receive attendance from a single employee

        Parameters:
        attendances (list): The list of employee attendance data to be transformed.

        Returns:
        dict: The transformed data.
        """
        employee = self.employee_id
        attendances = self.get_attendance()
        assert all(a.employee_id.id == employee.id for a in attendances)

        # Sort attendances by check_in date
        attendances = attendances.sorted(key=lambda x: (x.check_in))

        # Group attendances by employee_id and check_in date
        user_tz = self.env.user.tz or 'UTC'
        attendance_date = {
            _date: list(_attendance)
            for _date, _attendance in groupby(attendances, key=lambda x: convert_to_user_tz(x.check_in, user_tz).date())
            }

        report = {"header": {}, "rows": []}

        start_date = self.date_from
        end_date = self.date_to

        days = (end_date - start_date).days + 1
        ordinary_hours_max = days // 7 * 44 + days % 7 * 8
        # Calculate the number of full weeks and remaining days
        full_weeks = days // 7
        remaining_days = days % 7

        # Calculate the expected hours
        expected_hours = (full_weeks * 44) + (remaining_days * 8)

        # a list of dates between start_date and end_date
        dates = (
            start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)
            )

        attendances_report = []

        for _date in dates:
            attendances_report.append(self._process_date(employee, _date, attendance_date))

        report["rows"] = attendances_report

        ordinary_hours_days = min(sum(a["ordinary_hours"] for a in attendances_report), ordinary_hours_max)
        extra_hours_weeks = max(sum(a["extra_hours"] for a in attendances_report) - ordinary_hours_max, 0)

        report["header"] = {
            "employee_id": employee.id,
            "employee_no": employee.employee_no,
            "employee": employee.name,
            "start_date": start_date,
            "end_date": end_date,
            "expected_hours": expected_hours,
            "total_hours": sum(a["total_hours"] for a in attendances_report),
            "ordinary_hours": ordinary_hours_days,
            "extra_hours": sum(a["extra_hours"] for a in attendances_report) + extra_hours_weeks,
            "transport_bonus": sum(a["transport_bonus"] for a in attendances_report),
            }
        return report

    def _process_date(self, employee, _date, attendance_date):
        user_tz = self.env.user.tz or 'UTC'
        if _date not in attendance_date:
            return {
                "employee_id": employee.id,
                "employee_no": employee.employee_no,
                "employee": employee.name,
                "date": _date,
                "check_in_1": "",
                "check_out_1": "",
                "check_in_2": "",
                "check_out_2": "",
                "check_in_3": "",
                "check_out_3": "",
                "total_hours": 0,
                "ordinary_hours": 0,
                "extra_hours": 0,
                "observation": "No se registraron marcas este día.",
                "transport_bonus": 0,
                }
        attendances = attendance_date[_date]
        assert len(attendances) > 0, "There should be at least one attendance for the date."
        worked_hours, ordinary_hours, extra_hours = self._compute_hours(attendances)
        transport_bonus = self._compute_transport_bonus(attendances)
        observations = []
        if len(attendances) > 2:
            observations.append("More than 2 attendances for this date.")
        return {
            "employee_id": employee.id,
            "employee_no": employee.employee_no,
            "employee": employee.name,
            "date": _date,
            "check_in_1": convert_to_user_tz(attendances[0].check_in, user_tz) if attendances else "",
            "check_out_1": convert_to_user_tz(attendances[0].check_out, user_tz) if attendances else "",
            "check_in_2": convert_to_user_tz(attendances[1].check_in, user_tz) if len(attendances) > 1 else "",
            "check_out_2": convert_to_user_tz(attendances[1].check_out, user_tz) if len(attendances) > 1 else "",
            "check_in_3": convert_to_user_tz(attendances[2].check_in, user_tz) if len(attendances) > 2 else "",
            "check_out_3": convert_to_user_tz(attendances[2].check_out, user_tz) if len(attendances) > 2 else "",
            "total_hours": worked_hours,
            "ordinary_hours": ordinary_hours,
            "extra_hours": extra_hours,
            "observation": ", ".join(observations) if observations else "",
            "transport_bonus": transport_bonus,
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

    def _compute_transport_bonus(self, attendances):
        """
        Compute the transport bonus for an employee in a day.

        Parameters:
        attendances (list): The list of employee attendance data to be transformed.

        Returns:
        float: The transport bonus for the employee.
        """
        contract = self.employee_id.contract_id
        if not contract:
            return 0
        start_time_for_bonus = contract.early_checkin_bonus_time
        end_time_for_bonus = contract.late_checkout_bonus_time
        value_bonus = contract.value_bonus
        if value_bonus <= 0:
            return 0

        # Get the check-in and check-out times for the first attendance
        check_ins = [att.check_in for att in attendances]
        check_outs = [att.check_out for att in attendances]

        transport_bonus = 0
        if any(compare_datetime_with_float(check_in, start_time_for_bonus, '<') for check_in in check_ins):
            transport_bonus += value_bonus
        if any(compare_datetime_with_float(check_out, end_time_for_bonus, '>') for check_out in check_outs):
            transport_bonus += value_bonus

        return transport_bonus


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

    email = fields.Char('Email', required=True)

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
        footer_format = workbook.add_format(
            {"bold": True, "border": 1, "font_name": "Arial", "align": "left"}
            )
        return {
            "date_format": date_format,
            "header_format": header_format,
            "body_format": body_format,
            "body_date_format": body_date_format,
            "footer_format": footer_format,
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
        worksheet.write("A1", "Nombre de Empleado", formats["header_format"])
        worksheet.write("B1", data_header["employee"], formats["body_format"])
        worksheet.write("A2", "Código de Empleado", formats["header_format"])
        worksheet.write("B2", data_header["employee_no"], formats["body_format"])
        worksheet.write("A3", "Fecha Inicio", formats["header_format"])
        worksheet.write("B3", data_header["start_date"], formats["body_date_format"])
        worksheet.write("A4", "Fecha Fin", formats["header_format"])
        worksheet.write("B4", data_header["end_date"], formats["body_date_format"])
        worksheet.write("A5", "Horas Esperadas", formats["header_format"])
        worksheet.write("B5", data_header["expected_hours"], formats["body_format"])

    @staticmethod
    def _write_data_rows(worksheet, data_rows, body_format, body_date_format, start_row):
        row = start_row
        for data_row in data_rows:
            # Write the date and day of the week
            worksheet.write(row, 0, data_row["date"].strftime("%Y-%m-%d"), body_date_format)
            worksheet.write(row, 1, format_date(data_row["date"], "EEEE", locale="es"), body_format)

            # Write the check-in and check-out times for both shifts
            worksheet.write(
                row, 2, data_row["check_in_1"].strftime("%H:%M:%S") if data_row["check_in_1"] else "",
                body_format
                )
            worksheet.write(
                row, 3, data_row["check_out_1"].strftime("%H:%M:%S") if data_row["check_out_1"] else "",
                body_format
                )
            worksheet.write(
                row, 4, data_row["check_in_2"].strftime("%H:%M:%S") if data_row["check_in_2"] else "",
                body_format
                )
            worksheet.write(
                row, 5, data_row["check_out_2"].strftime("%H:%M:%S") if data_row["check_out_2"] else "",
                body_format
                )
            worksheet.write(
                row, 6, data_row["check_in_3"].strftime("%H:%M:%S") if data_row["check_in_3"] else "",
                body_format
                )
            worksheet.write(
                row, 7, data_row["check_out_3"].strftime("%H:%M:%S") if data_row["check_out_3"] else "",
                body_format
                )
            # Write the total, ordinary, and extra hours
            worksheet.write(row, 8, round(data_row["total_hours"], 2), body_format)
            worksheet.write(row, 9, data_row["ordinary_hours"], body_format)
            worksheet.write(row, 10, data_row["extra_hours"], body_format)

            # Write the observation and transport bonus
            worksheet.write(row, 11, data_row["observation"], body_format)
            worksheet.write(row, 12, data_row["transport_bonus"], body_format)

            row += 1
        return row

    @staticmethod
    def _process_excel_rows(
            data_rows,
            worksheet,
            formats,
            data_header,
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
            "Turno 2 (Entrada)",
            "Turno 2 (Salida)",
            "Turno 3 (Entrada)",
            "Turno 3 (Salida)",
            "Horas totales",
            "Horas ordinarias",
            "Horas extras",
            "Observaciones",
            "Bono de transporte",
            ]
        header_format = formats["header_format"]
        body_format = formats["body_format"]
        body_date_format = formats["body_date_format"]
        footer_format = formats["footer_format"]
        row = 6
        # Write the headers to the worksheet with the new format and set the column width
        for i, header in enumerate(headers):
            worksheet.write(row, i, header, header_format)
            worksheet.set_column(i, i, len(header) + 2)
        row += 1
        # Write the rows to the worksheet with the new format

        row = HrAttendanceEmployeesReport._write_data_rows(worksheet, data_rows, body_format, body_date_format, row)

        for col in range(0, 13):
            worksheet.write(row, col, "", footer_format)

        worksheet.write(row, 0, "Total", footer_format)

        worksheet.write(row, 8, round(data_header["total_hours"], 2), footer_format)
        worksheet.write(row, 9, data_header["ordinary_hours"], footer_format)
        worksheet.write(row, 10, data_header["extra_hours"], footer_format)

        # Write the observation and transport bonus
        worksheet.write(row, 12, data_header["transport_bonus"], footer_format)

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

        employee_attendances = self.get_attendance()
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
                employee_attendances = employee_report.get_attendance()
                employee_attendance_data = employee_report.process_employee_attendance()

                # Crear un archivo Excel en memoria para el empleado actual
                employee_output = io.BytesIO()
                workbook = xlsxwriter.Workbook(employee_output, {'in_memory': True})
                formats = self._excel_formats(workbook)
                worksheet = workbook.add_worksheet()

                data_header = employee_attendance_data["header"]
                self._process_excel_headers(data_header, worksheet, formats)

                data_rows = employee_attendance_data["rows"]
                self._process_excel_rows(data_rows, worksheet, formats, data_header)

                workbook.close()

                # Añadir el archivo Excel al archivo ZIP
                employee_name = employee_id.name
                zipf.writestr(f'Employee Attendance Report - {employee_name}.xlsx', employee_output.getvalue())

        output.seek(0)
        zip_content = output.read()
        output.close()

        # send by email
        try:
            if not self.email:
                raise UserError(_("No email address is specified."))

            # Prepare email content
            mail_values = {
                'subject': _("Informe de Asistencia de Empleados"),
                'email_to': self.email,
                'body_html': f"""
                    <html>
                        <head></head>
                        <body>
                            <p>Estimado/a,</p>
                            <p>Adjunto encontrará el Informe de Asistencia de Empleados correspondiente al período del 
                            {self.date_from} al {self.date_to}.</p>
                            <p>Este informe contiene información detallada sobre la asistencia de los empleados 
                            durante el período solicitado.</p>
                            <p>Si tiene alguna pregunta o necesita más información, no dude en contactarnos.</p>
                            <p>Saludos cordiales,</p>
                            <p>El equipo de Recursos Humanos</p>
                        </body>
                    </html>
                """,
                'attachment_ids': [(self.env['ir.attachment'].create(
                    {
                        'name': f'Employee Attendance Report - {self.date_from} - {self.date_to}.zip',
                        'datas': base64.b64encode(zip_content),
                        'type': 'binary',
                        'res_model': self._name,
                        }
                    ).id)],
                }
            self.env['mail.mail'].create(mail_values).send()
            return {"success": True, "message": _("The report was successfully sent to the specified email address.")}
        except Exception as e:
            return {"success": False, "message": str(e)}
