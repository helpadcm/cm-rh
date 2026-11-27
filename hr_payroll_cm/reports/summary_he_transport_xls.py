# -*- coding: utf-8 -*-
import time
import time
import base64
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from odoo import _, models
from io import BytesIO

class summaryHESTXLS(models.AbstractModel):
    _name = 'report.hr_payroll_cm.summary_eh_transport_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Resumen HE y ST XLS"
    
    def generate_xlsx_report(self, workbook, data, lines):
        xdata = self.get_data(lines)
        
        #titles
        format212 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False})
        format213 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': True, 'top': True, 'bold': True})
        format214 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False})
        format215 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#dadada',})
        format216 = workbook.add_format({'font_size': 13, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format217 = workbook.add_format({'font_size': 13, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#92D050', 'color': '#000000'})
        format218 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': True, 'top': False, 'bold': True})
        format219 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format220 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format511 = workbook.add_format({'font_size': 12, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        #numbers
        format41 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': ' #,###,##0.00'})
        format42 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': ' #,###,##0.00', 'bg_color': '#92D050'})
        format43 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': ' #,###,##0.00', 'bg_color': '#dadada'})

        format1 = workbook.add_format({'font_size': 14, 'bottom': False, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format2 = workbook.add_format({'font_size': 14, 'bottom': False, 'right': True, 'left': True, 'top': False, 'align': 'vcenter', 'bold': True})
        format4 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': False, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
        format111 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': False})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': False,'bottom': False, 'top': False, 'bold': True})

        format211 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': True, 'left': False,'bottom': True, 'top': True, 'bold': True, 'num_format':  '#,###,##0.#0'})
        format411 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': 'L #,###,##0.#0'})
        format412 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format':  '#,###,##0.#0'})
        format51 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': 'L #,###,##0.#0'})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
                                    'bg_color': 'red'})
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
        format3.set_align('center')
        font_size_8.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        format2.set_align('center')
        format4.set_align('center')
        red_mark.set_align('center')
        
        for period in xdata:
            sheet = workbook.add_worksheet(period.get('period'))
            period_name = period.get('period')
            sheet.set_column(0, 0, 5)
            sheet.set_column(1, 1, 8)
            sheet.set_column(2, 2, 35)
            sheet.set_column(3, 3, 15)
            sheet.set_column(4, 4, 15)
            sheet.set_column(5, 5, 15)
            sheet.set_column(6, 6, 15)
            sheet.set_column(8, 8, 15)
            sheet.set_column(9, 9, 15)
            sheet.set_column(10, 10, 15)
            sheet.set_column(11, 11, 15)
            sheet.set_column(12, 12, 15)
            pos=1

            t_total_eh = 0
            t_total_25 = 0
            t_total_50 = 0
            t_total_75 = 0
            t_total_real_eh = 0
            t_total_holiday = 0
            t_total_holiday_extra = 0
            t_total_tb_limit = 0
            t_total_tb_pay = 0
            
            title_line = "A" + str(pos) + ":" + "N" + str(pos)
            sheet.merge_range(title_line, period_name  + ' Resumen de HE y Subsidio de Transporte', format216)
            pos+=2
            for dep in period.get('datas'):
                title_partner = "A" + str(pos + 1) + ":" + "C" + str(pos + 1)
                sheet.merge_range(title_partner, dep.get('department'), format217)
                pos += 1
                sheet.write(pos, 0, _('#'), format213)
                sheet.write(pos, 1, _('Cód.'), format213)
                sheet.write(pos, 2, _('Empleado'), format213)
                sheet.write(pos, 3, _('Fecha de Inicio'), format213)
                sheet.write(pos, 4, _('Fecha Fin'), format213)
                sheet.write(pos, 5, _('HE Limite'), format213)
                sheet.write(pos, 6, _('HE 25%'), format213)
                sheet.write(pos, 7, _('HE 50%'), format213)
                sheet.write(pos, 8, _('HE 75%'), format213)
                sheet.write(pos, 9, _('HE Totales'), format213)
                sheet.write(pos, 10, _('Dias Feriado'), format213)
                sheet.write(pos, 11, _('HE Feriado'), format213)
                sheet.write(pos, 12, _('ST Limite'), format213)
                sheet.write(pos, 13, _('Pagar ST'), format213)
                pos += 1
                cont = 1

                total_eh = 0
                total_25 = 0
                total_50 = 0
                total_75 = 0
                total_real_eh = 0
                total_holiday = 0
                total_holiday_extra = 0
                total_tb_limit = 0
                total_tb_pay = 0

                for data in dep.get('values'):
                    sheet.write(pos, 0, cont, format215)
                    sheet.write(pos, 1, data.get('code'), format214)
                    sheet.write(pos, 2, data.get('employee'), format214)
                    sheet.write(pos, 3, data.get('start_date'), format214)
                    sheet.write(pos, 4, data.get('end_date'), format214)
                    sheet.write_number(pos, 5, data.get('limit_eh') or 0, format41)
                    sheet.write_number(pos, 6, data.get('eh_25') or 0, format41)
                    sheet.write_number(pos, 7, data.get('eh_50') or 0, format41)
                    sheet.write_number(pos, 8, data.get('eh_75') or 0, format41)
                    sheet.write_number(pos, 9, data.get('real_eh') or 0, format42)
                    sheet.write_number(pos, 10, data.get('eh_holiday') or 0, format42)
                    sheet.write_number(pos, 11, data.get('eh_holiday_extra') or 0, format42)
                    sheet.write_number(pos, 12, data.get('tb_limit') or 0, format41)
                    sheet.write_number(pos, 13, data.get('tb_pay') or 0, format42)
                    total_eh += data.get('limit_eh')
                    total_25 += data.get('eh_25')
                    total_50 += data.get('eh_50')
                    total_75 += data.get('eh_75')
                    total_real_eh += data.get('real_eh')
                    total_holiday += data.get('eh_holiday')
                    total_holiday_extra += data.get('eh_holiday_extra')
                    total_tb_limit += data.get('tb_limit')
                    total_tb_pay += data.get('tb_pay')

                    t_total_eh += data.get('limit_eh')
                    t_total_25 += data.get('eh_25')
                    t_total_50 += data.get('eh_50')
                    t_total_75 += data.get('eh_75')
                    t_total_real_eh += data.get('real_eh')
                    t_total_holiday += data.get('eh_holiday')
                    t_total_holiday_extra += data.get('eh_holiday_extra')
                    t_total_tb_limit += data.get('tb_limit')
                    t_total_tb_pay += data.get('tb_pay')
                    pos += 1
                    cont += 1
                
                title_partner = "A" + str(pos + 1) + ":" + "E" + str(pos + 1)
                sheet.merge_range(title_partner, 'TOTAL', format215)
                sheet.write_number(pos, 5, total_eh or 0, format43)
                sheet.write_number(pos, 6, total_25, format43)
                sheet.write_number(pos, 7, total_50, format43)
                sheet.write_number(pos, 8, total_75, format43)
                sheet.write_number(pos, 9, total_real_eh, format43)
                sheet.write_number(pos, 10, total_holiday, format43)
                sheet.write_number(pos, 11, total_holiday_extra, format43)
                sheet.write_number(pos, 12, total_tb_limit, format43)
                sheet.write_number(pos, 13, total_tb_pay, format43)
                pos += 2
            pos += 1
            title_partner = "A" + str(pos + 1) + ":" + "E" + str(pos + 1)
            sheet.merge_range(title_partner, 'TOTALES', format215)
            sheet.write_number(pos, 5, t_total_eh or 0, format43)
            sheet.write_number(pos, 6, t_total_25, format43)
            sheet.write_number(pos, 7, t_total_50, format43)
            sheet.write_number(pos, 8, t_total_75, format43)
            sheet.write_number(pos, 9, t_total_real_eh, format43)
            sheet.write_number(pos, 10, t_total_holiday, format43)
            sheet.write_number(pos, 11, t_total_holiday_extra, format43)
            sheet.write_number(pos, 12, t_total_tb_limit, format43)
            sheet.write_number(pos, 13, t_total_tb_pay, format43)


    def get_data(self, rec_ids):
        periods_map = {}

        for rec in rec_ids:
            eh_25 = rec.hours_25 if rec.hours_25 > 0 else rec.real_eh_pay

            vals = {
                'code': rec.code,
                'employee': rec.employee_id.name,
                'start_date': rec.start_date.strftime("%d/%m/%Y") if rec.start_date else '',
                'end_date': rec.end_date.strftime("%d/%m/%Y") if rec.end_date else '',
                'limit_eh': rec.eh_limit,
                'eh_25': eh_25,
                'eh_50': rec.hours_50,
                'eh_75': rec.hours_75,
                'real_eh': rec.real_eh_pay,
                'eh_holiday_extra': rec.eh_holiday_extra,
                'eh_holiday': rec.eh_holiday / 8.0,
                'tb_limit': rec.tb_limit,
                'tb_pay': rec.tb_pay,
            }

            # 1. Crear el contenedor del período si no existe (con su propio mapa de departamentos)
            if rec.period not in periods_map:
                periods_map[rec.period] = {
                    'period': rec.period,
                    'departments_map': {},
                }

            dept_map = periods_map[rec.period]['departments_map']
            dept_id = rec.department_id.id

            # 2. Dentro de ESE período, agrupar por departamento
            if dept_id not in dept_map:
                dept_map[dept_id] = {
                    'department': rec.department_id.name or 'Sin Departamento',
                    'values': [],
                }

            # 3. Agregar el registro del empleado al departamento de ese período
            dept_map[dept_id]['values'].append(vals)

        # 4. Convertir a la estructura final exacta que espera tu reporte
        period_datas = []
        for p_data in periods_map.values():
            period_datas.append({
                'period': p_data['period'],
                'datas': list(p_data['departments_map'].values()),
            })

        return period_datas