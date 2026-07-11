from odoo import models
import base64
import io

columns_letter = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G',
    'H', 'I', 'J', 'K', 'L', 'M', 'N',
    'O', 'P', 'Q', 'R', 'S', 'T', 'U',
    'V', 'W', 'X', 'Y', 'Z'
]

class incDedFormatXlsx(models.AbstractModel):
    _name = 'report.hr_payroll_cm.inc_ded_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Ingresos y Deducciones XLS"

    def generate_xlsx_report(self, workbook, data, docids):
        info = self.get_data(data)
        show_details = data.get('show_details')
        sheet = workbook.add_worksheet('Ingresos y Deducciones')

        # Obtener la empresa y el logo
        company = self.env.user.company_id
        if company.logo:
            image_data = io.BytesIO(base64.b64decode(company.logo))  # Decodificar logo
            sheet.insert_image('A1', 'logo.png', {'image_data': image_data, 'x_scale': 0.2, 'y_scale': 0.15})  # Ajustar tamaño


        # Formatos
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        header_format = workbook.add_format({'font_size': 10, 'bold': True, 'align': 'center', 'bg_color': '#58D68D', 'color': '#000000', 'border': 2, 'text_wrap':True})
        dept_format = workbook.add_format({'font_size': 12, 'bold': True, 'align': 'center', 'bg_color': '#58D68D', 'right': True, 'left': True})
        dept_name_format = workbook.add_format({'font_size': 12, 'bold': True, 'align': 'center', 'bg_color': '#58D68D', 'border': 1})
        emp_name_format = workbook.add_format({'font_size': 10, 'bold': True, 'align': 'center', 'border': 1})
        money_format = workbook.add_format({'font_size': 10, 'num_format': '#,##0.00','text_wrap':True,'right': True, 'left': True})
        totals_format = workbook.add_format({'font_size': 10, 'border': 1, 'bold': True, 'num_format': '#,##0.00', 'bg_color': '#58D68D'})
        emp_totals_format = workbook.add_format({'font_size': 10, 'border': 1, 'bold': True, 'num_format': '#,##0.00'})
        count_format = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True, 'right': True, 'left': True, 'color': '#FF0000'})
        total_totals_format = workbook.add_format({'font_size': 10, 'border': 1, 'bold': True, 'num_format': '#,##0.00', 'bg_color': '#58D68D'})

        count_format.set_align('center')
        header_format.set_align('center')
        header_format.set_align('vcenter')
        format1.set_align('center')

        company_name = company.name
        sheet.merge_range('D2:M2', company_name, format1)
        sheet.merge_range('D3:M3', "Ingresos/Deducciones", format1)

        # Columnas base
        headers = [
            'No.', 'Nomina', 'Empleado', 'Puesto'
        ]

        # Agregar reglas salariales dinámicamente
        if info.get('incomes_name'):
            headers += info.get('incomes_name', []) + ['Total Devengado']
        if info.get('deductions_name'):
            headers += info.get('deductions_name', []) + ['Total Deducciones']
        headers += ['TOTAL']

        # Escribir encabezados
        for col, header in enumerate(headers):
            sheet.write(6, col, header, header_format)
            if col == 0:
                sheet.set_column(col, col, 5)
            else:
                sheet.set_column(col, col, 15)


        row = 7
        emp_count = 1
        grand_totals = {name: 0 for name in headers[4:]}  # Acumulador para gran total

        # Iterar sobre departamentos y empleados agrupados
        for department_name, department_info in info.get('department_data').items():
            dept_totals = {name: 0 for name in headers[4:]}  # Acumulador para cada departamento
            for employee in department_info.get('employees'):
                total_ingresos = sum(x['amount'] for x in employee.get('incomes'))
                total_devengado = total_ingresos  # **CORREGIDO**
                total_deducciones = abs(sum(x['amount'] for x in employee.get('deductions')))
                total_neto = total_devengado - total_deducciones

                # Acumular valores al total del departamento
                if info.get('incomes_name'):
                    dept_totals['Total Devengado'] += total_devengado
                if info.get('deductions_name'):
                    dept_totals['Total Deducciones'] += total_deducciones
                dept_totals['TOTAL'] += total_neto

                for rule in info.get('incomes_name'):
                    amount = next((x['amount'] for x in employee.get('incomes') if x['rule_name'] == rule), 0)
                    dept_totals[rule] += amount

                for rule in info.get('deductions_name'):
                    amount = next((x['amount'] for x in employee.get('deductions') if x['rule_name'] == rule), 0)
                    dept_totals[rule] += amount

                if show_details:
                    # Escribir datos del empleado
                    sheet.write(row, 0, emp_count, count_format)
                    sheet.write(row, 1, employee.get('payslip_run_name'), money_format)
                    sheet.write(row, 2, employee.get('employee'), money_format)
                    sheet.write(row, 3, employee.get('job') or '', money_format)

                col = 4
                if info.get('incomes_name'):
                    for rule in info.get('incomes_name'):
                        amount = next((x['amount'] for x in employee.get('incomes') if x['rule_name'] == rule), 0)
                        if show_details:
                            if amount == 0:
                                sheet.write(row, col, '', money_format)
                            else:
                                sheet.write_number(row, col, amount, money_format)
                            col += 1

                    if show_details:
                        sheet.write_number(row, col, total_devengado, total_totals_format)  # **CORREGIDO**
                        col += 1

                if info.get('deductions_name'):
                    for rule in info.get('deductions_name'):
                        amount = abs(next((x['amount'] for x in employee.get('deductions') if x['rule_name'] == rule), 0))
                        if show_details:
                            if amount == 0:
                                sheet.write(row, col, '', money_format)
                            else:
                                sheet.write_number(row, col, amount, money_format)
                            col += 1
                    if show_details:
                        sheet.write_number(row, col, total_deducciones, total_totals_format)
                        col += 1

                if show_details:
                    sheet.write_number(row, col, total_neto, money_format)

                    row += 1
                emp_count += 1

            # Escribir totales del departamento
            if show_details:
                sheet.merge_range('A%s:D%s'%(row+1,row+1), department_name, dept_name_format)
            else:
                sheet.merge_range('A%s:D%s'%(row+1,row+1), department_name, emp_name_format)

            col = 4
            for key in headers[4:]:
                if show_details:
                    sheet.write_number(row, col, abs(dept_totals[key]), totals_format)
                else:
                    sheet.write_number(row, col, abs(dept_totals[key]), emp_totals_format)
                grand_totals[key] += dept_totals[key]  # Acumulamos en el gran total general
                col += 1
            row += 1

        # Gran total general en la última fila
        row+=3
        sheet.merge_range('A%s:D%s'%(row+1,row+1), 'GRAN TOTAL GENERAL', dept_name_format)
        col = 4
        for key in headers[4:]:
            sheet.write_number(row, col, grand_totals[key], total_totals_format)
            col += 1
            

    def get_data(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        employee_ids = data.get('employee_ids')
        incomes_code = data.get('incomes_rules')
        deductions_code = data.get('deductions_rules')

        employees_dict = {}
        deductions_name = []
        incomes_name = []

        if employee_ids:
            payslips = self.env['hr.payslip'].search([('date_from', '>=', start_date),('date_to', '<=', end_date),('employee_id','in',employee_ids)])
        else:
            payslips = self.env['hr.payslip'].search([('date_from', '>=', start_date),('date_to', '<=', end_date)])
        payslip_name = ''
        for payslip in payslips:
            employees_name = payslip.employee_id.name
            deductions = []
            incomes = []
            overtime_amount = 0
            payslip_name = payslip.payslip_run_id.name

            if payslip.worked_days_line_ids:
                for entry in payslip.worked_days_line_ids:
                    if entry.work_entry_type_id.code == 'OVERTIME':
                        overtime_amount += entry.amount

                    if entry.work_entry_type_id.code in incomes_code:
                        if entry.work_entry_type_id.name not in incomes_name:
                            incomes_name.append(entry.work_entry_type_id.name)
                        incomes.append({'rule_name': entry.work_entry_type_id.name, 'amount': entry.amount, 'code': entry.work_entry_type_id.code})

                    if entry.work_entry_type_id.code in deductions_code:
                        if entry.work_entry_type_id.name not in deductions_name:
                            deductions_name.append(entry.work_entry_type_id.name)
                        deductions.append({'rule_name': entry.work_entry_type_id.name, 'amount': entry.amount, 'code': entry.work_entry_type_id.code})

            for line in payslip.line_ids:
                if line.salary_rule_id.code in incomes_code:
                    if line.salary_rule_id.name not in incomes_name:
                        incomes_name.append(line.salary_rule_id.name)
                    incomes.append({'rule_name': line.salary_rule_id.name, 'amount': line.total, 'code': line.salary_rule_id.code})

                if line.salary_rule_id.code in deductions_code:
                    if line.salary_rule_id.name not in deductions_name:
                        deductions_name.append(line.salary_rule_id.name)
                    deductions.append({'rule_name': line.salary_rule_id.name, 'amount': line.total, 'code': line.salary_rule_id.code})
            
            for item in incomes:
                if item['code'] == 'BASIC':
                    item['amount'] -= overtime_amount

            employee_vals = {
                'payslip_run_name': payslip.payslip_run_id.name,
                'identity': payslip.contract_id.employee_id.identification_id,
                'bank_account': payslip.contract_id.employee_id.bank_account_id.acc_number,
                'employee': payslip.employee_id.name,
                'job': payslip.employee_id.job_id.name,
                'monthly_salary': payslip.contract_id.wage * 2,
                'salary': payslip.contract_id.wage,
                'deductions': deductions,
                'incomes': incomes
            }

            if employees_name not in employees_dict:
                employees_dict[employees_name] = {'employees': []}
            employees_dict[employees_name]['employees'].append(employee_vals)

        return {'department_data': employees_dict, 'deductions_name': deductions_name, 'incomes_name': incomes_name, 'payslip_name': payslip_name}
