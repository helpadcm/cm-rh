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
            nombre_de_empleado=employee_id.name,
            puesto_del_empleado=employee_id.job_id.name,
            salario_mensual=employee_id.contract_id.wage or 0.0,
            salario_quincenal=employee_id.contract_id.wage / 2 or 0.0
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
        return PaySlipReportDataClass(
            ihss=paysliplines_ids.filtered(lambda x: x.code == 'SSH').amount
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

    def _payslip_records_to_excel(self, worksheet, payslip_records, department_name, row_num=1):
        """
        This method converts the payslip records to an excel sheet
        :param payslip_records: 
        :return: 
        """
        for record in payslip_records:
            worksheet.write(row_num, 0, record.no)
            worksheet.write(row_num, 1, record.fecha_de_ingreso)
            worksheet.write(row_num, 2, record.id)
            worksheet.write(row_num, 3, record.no_de_cuenta_ban_pais)
            worksheet.write(row_num, 4, record.nombre_de_empleado)
            worksheet.write(row_num, 5, record.puesto_del_empleado)
            worksheet.write(row_num, 6, record.salario_mensual)
            worksheet.write(row_num, 7, record.salario_quincenal)
            worksheet.write(row_num, 8, record.horas_extras_125)
            worksheet.write(row_num, 9, record.valor_tiempo_extra_25)
            worksheet.write(row_num, 10, record.bono_de_transporte_alimentacion_capacitacion)
            worksheet.write(row_num, 11, record.charter_comisones)
            worksheet.write(row_num, 12, record.bono_por_resultado)
            worksheet.write(row_num, 13, record.total_devengado)
            worksheet.write(row_num, 14, record.isr)
            worksheet.write(row_num, 15, record.rap)
            worksheet.write(row_num, 16, record.ihss)
            worksheet.write(row_num, 17, record.impto_vecinal)
            worksheet.write(row_num, 18, record.elga)
            worksheet.write(row_num, 19, record.prestamos_internos)
            worksheet.write(row_num, 20, record.cuentas_por_cobrar)
            worksheet.write(row_num, 21, record.prestamos_rap)
            worksheet.write(row_num, 22, record.odontologia)
            worksheet.write(row_num, 23, record.optica)
            worksheet.write(row_num, 24, record.incapacidad_1)
            worksheet.write(row_num, 25, record.incapacidad_2)
            worksheet.write(row_num, 26, record.total_deducciones)
            worksheet.write(row_num, 27, record.total_neto_a_pagar)
            row_num += 1

        # Write totals
        worksheet.write(row_num, 0, 'Total')
        worksheet.write(row_num, 4, department_name)
        worksheet.write(row_num, 6, f'=SUM(G2:G{row_num})')
        worksheet.write(row_num, 7, f'=SUM(H2:H{row_num})')
        worksheet.write(row_num, 13, f'=SUM(N2:N{row_num})')
        worksheet.write(row_num, 14, f'=SUM(O2:O{row_num})')
        worksheet.write(row_num, 15, f'=SUM(P2:P{row_num})')
        worksheet.write(row_num, 16, f'=SUM(Q2:Q{row_num})')
        worksheet.write(row_num, 17, f'=SUM(R2:R{row_num})')
        worksheet.write(row_num, 18, f'=SUM(S2:S{row_num})')
        worksheet.write(row_num, 19, f'=SUM(T2:T{row_num})')
        worksheet.write(row_num, 20, f'=SUM(U2:U{row_num})')
        worksheet.write(row_num, 21, f'=SUM(V2:V{row_num})')
        worksheet.write(row_num, 22, f'=SUM(W2:W{row_num})')
        worksheet.write(row_num, 23, f'=SUM(X2:X{row_num})')
        worksheet.write(row_num, 24, f'=SUM(Y2:Y{row_num})')
        worksheet.write(row_num, 25, f'=SUM(Z2:Z{row_num})')
        worksheet.write(row_num, 26, f'=SUM(AA2:AA{row_num})')
        worksheet.write(row_num, 27, f'=SUM(AB2:AB{row_num})')

        return row_num + 1

    def _create_sheet_for_contract_type(self, workbook, contract_type, payslips_records_by_department):
        """
        This method creates a sheet for a contract type
        :param workbook: 
        :param contract_type: 
        :param payslips: 
        :return: 
        """
        worksheet = workbook.add_worksheet(contract_type)

        headers = PaySlipReport._fields
        for index, header in enumerate(headers):
            worksheet.write(0, index, header)

        # payslips_by_department = self._process_payslips_by_contract_type(payslips)
        row_num = 1
        for department, payslips in payslips_records_by_department.items():
            row_num = self._payslip_records_to_excel(worksheet, payslips, department, row_num)

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
