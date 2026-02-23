# -*- coding: utf-8 -*-
import time
import random
import time
import base64
from datetime import datetime, timedelta
from odoo import _, models
from io import BytesIO

days = [
    "Lunes", "Martes", "Miércoles",
    "Jueves", "Viernes", "Sábado", "Domingo"
]

class attendanceTeamXLS(models.AbstractModel):
    _name = 'report.hr_turns_cm.report_attendance_team_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Asistencia de equipos XLS"
    
    def generate_xlsx_report(self, workbook, data, lines): 	
        xdata = self.get_data(data)
        
        #titles
        format213 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': True, 'top': True, 'bold': True})
        format214 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format215 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True, 'bg_color': '#dadada',})
        format216 = workbook.add_format({'font_size': 13, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format217 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': True,'bottom': True, 'top': False, 'bold': True})
        format218 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': True, 'top': False, 'bold': True})
        format219 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format220 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        format511 = workbook.add_format({'font_size': 12, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
        #numbers
        format41 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': ' #,###,##0.00'})

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
        
        for emp in xdata:
            date_list = []
            sheet = workbook.add_worksheet(emp.get('employee'))
            sheet.set_column(0, 0, 15)
            sheet.set_column(1, 1, 15)
            sheet.set_column(2, 2, 25)
            sheet.set_column(3, 3, 25)
            pos=1
            
            pos_image = "A"+str(pos)
            image_data = BytesIO(base64.b64decode(self.env.user.company_id.logo))
            sheet.insert_image(pos_image,'logo',{'image_data':image_data,'x_scale': 0.1,'y_scale': 0.1,'x_offset':50})
            title_line = "A" + str(pos) + ":" + "H" + str(pos)
            sheet.merge_range(title_line, _('ASISTENCIA DE %s'%(emp.get('employee'))), format216)  
            sheet.write(pos + 1, 2, _('Desde: %s')%(data.get('initial_date')), format219)
            sheet.write(pos + 1, 3, _('Al: %s')%(data.get('final_date')), format219)
            pos+=4

            sheet.write(pos, 0, _('Fecha'), format213)
            sheet.write(pos, 1, _('Dia'), format213)
            sheet.write(pos, 2, _('Fecha de Entrada'), format213)
            sheet.write(pos, 3, _('Fecha de Salida'), format213)
            pos+=1
            for o in emp.get('marks'):
                if not o.get('date') in date_list:
                    date_list.append(o.get('date'))
                    bg_color = self.random_soft_hex()

                format212 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False, 'bg_color': bg_color})
                sheet.write(pos, 0, o.get('date'), format212)
                sheet.write(pos, 1, o.get('day') or '', format212)
                sheet.write(pos, 2, o.get('check_in'), format212)
                sheet.write(pos, 3, o.get('check_out'), format212)
                pos += 1


    def get_data(self, data):
        team_id = self.env['hr.work.teams'].browse(data.get('team_id'))
        initial_date = data.get('initial_date')
        final_date = data.get('final_date')

        start_date = datetime.strptime(initial_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
        end_date = datetime.strptime(final_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

        employee_ids = team_id.member_employees_ids.mapped('employee_id')
        attendance_ids = self.env['hr.attendance'].search([('check_in','>=',start_date),('check_out','<=',end_date),('employee_id','in',employee_ids.ids)], order="check_in asc")

        data = []
        list_employee_ids = []
        for att in attendance_ids:
            vals = {
                'date': att.check_in.strftime('%d/%m/%Y'),
                'day': days[att.check_in.weekday()],
                'check_in': (att.check_in - timedelta(hours=6)).strftime('%H:%M:%S'),
                'check_out': (att.check_out - timedelta(hours=6)).strftime('%H:%M:%S')
            }
            if att.employee_id.id in list_employee_ids:
                data[list_employee_ids.index(att.employee_id.id)]['marks'].append(vals)
            else:
                list_employee_ids.append(att.employee_id.id)
                data.append({
                    'employee': att.employee_id.name,
                    'marks': [vals]
                })
        return data

    def random_soft_hex(self):
        return "#{:02X}{:02X}{:02X}".format(
            random.randint(170, 230),
            random.randint(170, 230),
            random.randint(170, 230),
        )