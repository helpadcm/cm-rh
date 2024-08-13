from collections import namedtuple

from odoo import models, fields

PaySlipReport = namedtuple(
    'PaySlipReport', [
        'No',
        'Fecha_de_Ingreso',
        'ID',
        'No_de_Cuenta_BAN_PAIS',
        'Nombre_de_Empleado',
        'Puesto_del_Empleado',
        'Salario_Mensual',
        'Salario_Quincenal',
        'Horas_Extras_1_25',
        'Valor_Tiempo_Extra_25',
        'Bono_de_Transporte_alimentacion_capacitacion',
        'Charter_Comisones',
        'Bono_Por_Resultado',
        'Total_Devengado',
        'ISR',
        'Rap',
        'IHSS',
        'Impto_Vecinal',
        'ELGA',
        'Prestamos_Internos',
        'Cuentas_por_Cobrar',
        'Prestamos_Rap',
        'Odontologia',
        'Optica',
        'Incapacidad_1',
        'Incapacidad_2',
        'Total_Deducciones',
        'TOTAL_NETO_A_PAGAR'
        ]
    )

ReportGroup = namedtuple(
    'ReportGroup', [
        'department',
        'total',
        'payslips'
        ]
    )


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

    lot_id = fields.Many2one('hr.payslip.run', string='Payroll Batch', required=True)
    payslips_ids = fields.One2many('hr.payslip', 'payslip_run_id', string='Payslips', related='lot_id.slip_ids')
    file = fields.Binary('File')
    name = fields.Char('File Name', size=64)

    def _get_work_lines(self, payslip):
        pass

    def _get_input_lines(self, payslip):
        pass

    def _get_payslip_lines(self, payslip):
        pass

    def _get_payslip_record_from_payslip(self, payslip, no, worklines, inputlines, paysliplines):
        pass

    def process_payslip(self, payslip, no=1):
        """
        This method processes the payslip and returns a PaySlipReport object
        :param no: 
        :param payslip: 
        :return: 
        """
        worklines = self._get_work_lines(payslip)
        inputlines = self._get_input_lines(payslip)
        paysliplines = self._get_payslip_lines(payslip)

        payslip_record = self._get_payslip_record_from_payslip(
            payslip,
            no,
            worklines,
            inputlines,
            paysliplines,
            )

        return payslip_record

    def _get_departments_from_payslips(self):
        """
        This method gets the departments from the payslips
        :return: 
        """
        return self.payslips_ids.mapped('employee_id.department_id.name')

    def _create_workbook_from_payslip_records(self, payslip_records):
        pass

    def export_to_excel(self, workbook):
        pass

    def process_payslip(self):
        """
        This method gets the payslips from the lot
        and processes each payslip resulting in a workbook with every payslip in a row.
        Additionally, calculates the total for each department.
        :return: 
        """
        departments = self._get_departments_from_payslips()

        payslip_records = []
        for department in departments:
            report_group = ReportGroup(department, 0, [])
            payslips_by_department = self.payslips_ids.filtered(lambda p: p.employee_id.department_id.name == department)
            for payslip in payslips_by_department:
                payslip_records.append(self.process_payslip(payslip))
                report_group.total += payslip.net_pay
                report_group.payslips.append(payslip)
            payslip_records.append(report_group)

        workbook = self._create_workbook_from_payslip_records(payslip_records)
        self.export_to_excel(workbook)
