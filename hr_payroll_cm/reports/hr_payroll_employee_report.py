import base64
import io

import xlsxwriter

from odoo import models, fields, api
from ..models.payslip_report import PaySlipReportDataClass, PaySlipReport


class HrPayrollPayslipsReport(models.TransientModel):
    """
    Employee Payroll Payslips Report.
    Its a wizard to generate the report.
    Its purpose is to generate the report in excel format for the use of finance department.
    Its conaints all the payslips from a lot 

    The result will contain the following columns:
    No., Fecha de Ingreso, ID, N° de Cuenta BAN PAIS, Nombre de Empleado, Puesto del Empleado, Salario Mensual, 
    Salario Quincenal, Horas Extras 1.25%, Valor Tiempo Extra 25%, Bono de Transporte/ alimentacion/ capacitacion, 
    Charter/ Comisones, Bono Por Resultado, Total Devengado, ISR, Rap, IHSS, Impto Vecinal, ELGA, Prestamos Internos, 
    Cuentas por Cobrar, Prestamos Rap, Odontologia, Optica, Incapacidad, Incapacidad, Total Deducciones, TOTAL NETO A 
    PAGAR

    """
    _name = "hr.payroll.payslips.report"
    _description = "reporte de nomina"

    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payroll Batch', required=True)
    payslips_ids = fields.One2many('hr.payslip', 'payslip_run_id', string='Payslips', related='payslip_run_id.slip_ids')
    file = fields.Binary('File', attachment=True)
    name = fields.Char('File Name', size=64, default='Payslips.xlsx')

    @api.onchange('payslip_run_id')
    def _onchange_payslip_run_id(self):
        """
        This method is called when the payslip_run_id changes
        :return: 
        """
        self.name = f'Payslips_{self.payslip_run_id.name}.xlsx'

    def _get_employee_data(self, payslip):
        """
        This method gets the employee data from the payslip
        returns a PaySlipReport object with 
        'Fecha_de_Ingreso',
        'ID',
        'No_de_Cuenta_BAN_PAIS',
        'Nombre_de_Empleado',
        'Puesto_del_Empleado',
        'Salario_Mensual',
        'Salario_Quincenal'
        :param payslip: 
        :return: 
        """
        employee_id = self.env["hr.employee"].search([('id', '=', payslip.employee_id.id)])
        return PaySlipReportDataClass(
            fecha_de_ingreso=employee_id.contract_id.date_start or '',
            id=employee_id.identification_id or '',
            no_de_cuenta_ban_pais=employee_id.bank_account_id.acc_number or '',
            nombre_de_empleado=employee_id.name or '',
            puesto_del_empleado=employee_id.job_id.name or '',
            salario_mensual=employee_id.contract_id.wage * 2 or 0.0,
            salario_quincenal=employee_id.contract_id.wage or 0.0
            )

    def _get_work_lines(self, payslip):
        """
        Return the work lines from the payslip
        horas_extras_125
        valor_tiempo_extra_25
        horas_extras_150
        valor_tiempo_extra_50-
        :param payslip: 
        :return: 
        """
        workline_ids = payslip.worked_days_line_ids
        return PaySlipReportDataClass(
            horas_extras_125=workline_ids.filtered(lambda x: x.code == 'HE125').number_of_hours,
            valor_tiempo_extra_25=workline_ids.filtered(lambda x: x.code == 'HE125').amount,
            horas_extras_150=workline_ids.filtered(lambda x: x.code == 'HE150').number_of_hours,
            valor_tiempo_extra_50=workline_ids.filtered(lambda x: x.code == 'HE150').amount
            )

    def _get_input_lines(self, payslip):
        """
        Return the input lines from the payslip
        feriado_trabajado
        bono_de_transporte_alimentacion_capacitacion
        charter_comisones
        bono_por_resultado
        ajuste
        isr
        rap
        impto_vecinal
        elga
        prestamos_internos
        cuentas_por_cobrar
        prestamos_rap
        odontologia
        optica
        incapacidad_1
        :param payslip: 
        :return: 
        """
        inputline_ids = payslip.input_line_ids
        return PaySlipReportDataClass(
            feriado_trabajado=inputline_ids.filtered(lambda x: x.code == 'HDT').amount,
            bono_de_transporte_alimentacion_capacitacion=inputline_ids.filtered(
                lambda x: x.code == 'TRANSBONUS'
                ).amount,
            charter_comisones=inputline_ids.filtered(lambda x: x.code == 'CHT').amount,
            bono_por_resultado=inputline_ids.filtered(lambda x: x.code == 'BPR').amount,
            ajuste=inputline_ids.filtered(lambda x: x.code == 'AJU').amount,
            isr=inputline_ids.filtered(lambda x: x.code == 'ISR').amount,
            rap=inputline_ids.filtered(lambda x: x.code == 'RAP').amount,
            impto_vecinal=inputline_ids.filtered(lambda x: x.code == 'IMV').amount,
            elga=inputline_ids.filtered(lambda x: x.code == 'CACELLOANS').amount,
            prestamos_internos=inputline_ids.filtered(lambda x: x.code == 'LOANS').amount,
            cuentas_por_cobrar=inputline_ids.filtered(lambda x: x.code == 'CXC').amount,
            prestamos_rap=inputline_ids.filtered(lambda x: x.code == 'RAPLOAN').amount,
            odontologia=inputline_ids.filtered(lambda x: x.code == 'ODT').amount,
            optica=inputline_ids.filtered(lambda x: x.code == 'SANTALUCIA').amount +
                   inputline_ids.filtered(lambda x: x.code == 'REYDEREYES').amount,
            incapacidad_1=inputline_ids.filtered(lambda x: x.code == 'IN1').amount,
            incapacidad_2=inputline_ids.filtered(lambda x: x.code == 'IN2').amount
            )

    def _get_payslip_lines(self, payslip):
        """
        Return the payslip lines from the payslip
        ihss
        :param payslip: 
        :return: 
        """
        paysliplines_ids = payslip.line_ids
        deduction_lines_ids = paysliplines_ids.filtered(lambda x: x.category_id.code == 'DED')
        total_deducciones = sum(abs(amount) for amount in deduction_lines_ids.mapped('amount'))
        return PaySlipReportDataClass(
            ihss=abs(paysliplines_ids.filtered(lambda x: x.code == 'SSH').amount),
            total_devengado=paysliplines_ids.filtered(lambda x: x.code == 'Gross').amount,
            total_deducciones=total_deducciones,
            total_neto_a_pagar=paysliplines_ids.filtered(lambda x: x.code == 'NET').amount,
            )

    def _get_payslip_record_from_payslip(self, payslip, no):
        """
        This method gets the payslip record from the payslip and a series of functions
        returning the merged values from the payslip without no
        :param payslip: 
        :param no:
        :return: 
        """
        employee_data = self._get_employee_data(payslip)
        worklines = self._get_work_lines(payslip)
        inputlines = self._get_input_lines(payslip)
        paysliplines = self._get_payslip_lines(payslip)

        ps_record = (PaySlipReportDataClass(no=no)
                     .update_not_none(employee_data)
                     .update_not_none(worklines)
                     .update_not_none(inputlines)
                     .update_not_none(paysliplines))

        return ps_record

    def _process_payslips(self, payslips, no=1):
        """
        This method processes the payslip and returns a PaySlipReport object
        :param no: 
        :param payslip: 
        :return: 
        """
        payslip_records = []
        for payslip in payslips:
            payslip_records.append(self._get_payslip_record_from_payslip(payslip, no))
            no += 1
        return payslip_records

    def _get_departments_from_payslips(self, payslips):
        """
        This method gets the departments from the payslips
        :return: 
        """
        return payslips.mapped('employee_id.department_id')

    def _process_payslips_by_contract_type(self, payslips):
        """
        This method processes the payslips by contract type
        group paylips by department and process each group
        :param payslips: 
        :return:  
        """
        departments = self._get_departments_from_payslips(payslips)
        payslips_grouped = {}
        for department in departments:
            payslips_grouped[department.name] = payslips.filtered(lambda x: x.employee_id.department_id == department)
        payslip_records = {}
        for department, payslips in payslips_grouped.items():
            payslip_records[department] = self._process_payslips(payslips)
        return payslip_records

    def _process_payslip_run(self):
        """
        This method processes the payslip run and returns a PaySlipReport object
        :return: 
        """
        contracts_type_ids = self.payslips_ids.mapped('employee_id.contract_id.structure_type_id')
        payslips_grouped = {}
        for contract_type in contracts_type_ids:
            payslips_grouped[contract_type.name] = self.payslips_ids.filtered(
                lambda x: x.employee_id.contract_id.structure_type_id == contract_type
                )
        payslip_records = {}
        for contract_type, payslips in payslips_grouped.items():
            payslip_records[contract_type] = self._process_payslips_by_contract_type(payslips)
        return payslip_records

    def _payslip_records_to_excel(self, worksheet, payslip_records, department_name, format_dict, row_num=1):
        """
        This method converts the payslip records to an excel sheet
        :param payslip_records: 
        :return: 
        """
        pair_format = format_dict['light_green']
        odd_format = format_dict['pastel_green']
        department_format = format_dict['bold_header']
        pair_currency_format = format_dict['currency_format_light_green']
        odd_currency_format = format_dict['currency_format_pastel_green']
        department_currency_format = format_dict['currency_format_bold_header']

        _row_num = row_num
        for record in payslip_records:
            if _row_num % 2 == 0:
                base_format = pair_format
                currency_format = pair_currency_format
            else:
                base_format = odd_format
                currency_format = odd_currency_format
            worksheet.write(_row_num, 0, record.no, base_format)
            worksheet.write(_row_num, 1, record.fecha_de_ingreso, base_format)
            worksheet.write(_row_num, 2, record.id, base_format)
            worksheet.write(_row_num, 3, record.no_de_cuenta_ban_pais, base_format)
            worksheet.write(_row_num, 4, record.nombre_de_empleado, base_format)
            worksheet.write(_row_num, 5, record.puesto_del_empleado, base_format)
            worksheet.write(_row_num, 6, record.salario_mensual, currency_format)
            worksheet.write(_row_num, 7, record.salario_quincenal, currency_format)
            worksheet.write(_row_num, 8, record.horas_extras_125, currency_format)
            worksheet.write(_row_num, 9, record.valor_tiempo_extra_25, currency_format)
            worksheet.write(_row_num, 10, record.bono_de_transporte_alimentacion_capacitacion, currency_format)
            worksheet.write(_row_num, 11, record.charter_comisones, currency_format)
            worksheet.write(_row_num, 12, record.bono_por_resultado, currency_format)
            worksheet.write(_row_num, 13, f'=SUM(H{_row_num + 1}:M{_row_num + 1})', currency_format)
            worksheet.write(_row_num, 14, record.isr, currency_format)
            worksheet.write(_row_num, 15, record.rap, currency_format)
            worksheet.write(_row_num, 16, record.ihss, currency_format)
            worksheet.write(_row_num, 17, record.impto_vecinal, currency_format)
            worksheet.write(_row_num, 18, record.elga, currency_format)
            worksheet.write(_row_num, 19, record.prestamos_internos, currency_format)
            worksheet.write(_row_num, 20, record.cuentas_por_cobrar, currency_format)
            worksheet.write(_row_num, 21, record.prestamos_rap, currency_format)
            worksheet.write(_row_num, 22, record.odontologia, currency_format)
            worksheet.write(_row_num, 23, record.optica, currency_format)
            worksheet.write(_row_num, 24, record.incapacidad_1, currency_format)
            worksheet.write(_row_num, 25, record.incapacidad_2, currency_format)
            worksheet.write(_row_num, 26, f'=SUM(O{_row_num + 1}:Z{_row_num + 1})', currency_format)
            worksheet.write(_row_num, 27, f'=N{_row_num + 1}-AA{_row_num + 1}', currency_format)
            _row_num += 1

        # Write totals
        currency_format = department_currency_format
        worksheet.write(_row_num, 0, 'Total', department_format)
        worksheet.write(_row_num, 4, department_name, department_format)
        worksheet.write(_row_num, 6, f'=SUM(G{row_num + 1}:G{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 7, f'=SUM(H{row_num + 1}:H{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 13, f'=SUM(N{row_num + 1}:N{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 14, f'=SUM(O{row_num + 1}:O{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 15, f'=SUM(P{row_num + 1}:P{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 16, f'=SUM(Q{row_num + 1}:Q{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 17, f'=SUM(R{row_num + 1}:R{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 18, f'=SUM(S{row_num + 1}:S{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 19, f'=SUM(T{row_num + 1}:T{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 20, f'=SUM(U{row_num + 1}:U{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 21, f'=SUM(V{row_num + 1}:V{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 22, f'=SUM(W{row_num + 1}:W{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 23, f'=SUM(X{row_num + 1}:X{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 24, f'=SUM(Y{row_num + 1}:Y{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 25, f'=SUM(Z{row_num + 1}:Z{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 26, f'=SUM(AA{row_num + 1}:AA{_row_num + 1})', currency_format)
        worksheet.write(_row_num, 27, f'=SUM(AB{row_num + 1}:AB{_row_num + 1})', currency_format)

        return _row_num + 1

    def _create_sheet_for_contract_type(self, workbook, contract_type, payslips_records_by_department):
        """
        This method creates a sheet for a contract type
        :param workbook: 
        :param contract_type: 
        :param payslips: 
        :return: 
        """
        worksheet = workbook.add_worksheet(contract_type)
        formats_dict = {
            'bold_header': workbook.add_format({'bold': True, 'bg_color': '#d3d3d3'}),
            'center': workbook.add_format({'align': 'center'}),
            'pastel_green': workbook.add_format({'bg_color': '#77dd77'}),
            'light_green': workbook.add_format({'bg_color': '#b2fab4'}),
            'light_gray': workbook.add_format({'bg_color': '#d3d3d3'}),
            'gray': workbook.add_format({'bg_color': '#a9a9a9'}),
            'currency_format_bold_header': workbook.add_format({'num_format': 'L#,##0.00', 'bg_color': '#d3d3d3'}),
            'currency_format_pastel_green': workbook.add_format({'num_format': 'L#,##0.00', 'bg_color': '#77dd77'}),
            'currency_format_light_green': workbook.add_format({'num_format': 'L#,##0.00', 'bg_color': '#b2fab4'}),
            'currency_format_light_gray': workbook.add_format({'num_format': 'L#,##0.00', 'bg_color': '#d3d3d3'}),

            }

        headers = PaySlipReport._fields
        for index, header in enumerate(headers):
            worksheet.write(0, index, header)
        worksheet.set_row(0, cell_format=formats_dict['bold_header'])
        worksheet.freeze_panes(1, 0)

        row_num = 1
        for department, payslips in payslips_records_by_department.items():
            row_num = self._payslip_records_to_excel(worksheet, payslips, department, formats_dict, row_num)

    def _create_workbook_from_payslip_records(self):
        """
        This method creates a workbook from the payslip records.
        For each contract type it creates a sheet with the payslip records
        then returns the workbook
        :return:
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        payslip_records = self._process_payslip_run()
        for contract_type, payslips_records_by_dpt in payslip_records.items():
            self._create_sheet_for_contract_type(workbook, contract_type, payslips_records_by_dpt)
        workbook.close()

        output.seek(0)
        xlsx_data = output.read()
        output.close()
        encoded_data = base64.b64encode(xlsx_data)
        self.file = encoded_data
        return self.env['ir.attachment'].create(
            {
                'name': f'Payslips_{self.payslip_run_id.name}.xlsx',
                'type': 'binary',
                'datas': encoded_data,
                'store_fname': f'Payslips_{self.payslip_run_id.name}.xlsx',
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                }
            )

    def process_payslip(self):
        """
        This method gets the payslips from the lot
        and processes each payslip resulting in a workbook with every payslip in a.
        Is mean to be used as a button in the view
        """
        self.ensure_one()
        attachment = self._create_workbook_from_payslip_records()
        # self.name = f'Payslips_{self.payslip_run_id.name}.xlsx'
        if not self.file:
            raise ValueError('No file was created')
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
            }
