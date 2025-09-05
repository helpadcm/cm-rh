import datetime
from odoo import models, _
import time

class GeneralLegderReport(models.AbstractModel):
	_name = 'report.cm_reports.general_invoice_xls'
	_inherit = 'report.report_xlsx.abstract'
	_description = "Reporte de Facturas XLS"

	def get_lines(self, data, docids):
		report_ob = self.env.get('report.cm_reports.general_invoice')
		lines = report_ob.render_xls( docids, data=data)
		return lines
		
	def generate_xlsx_report(self, workbook, data, lines): 	
		xlines=self.get_lines(data,lines)
		sheet = workbook.add_worksheet()
		format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
		format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
		format111 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': False})
		format21 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': False})
		format211 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
		format212 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': False, 'left': False,'bottom': False, 'top': False, 'bold': True})
		fnum = ' #,###,##0.00'
		format41 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format':fnum })
		format42 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': '#,###,##0.00'})
		format411 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': fnum})
		format412 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format':  '#,###,##0.#0'})
		format51 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': fnum})
		format511 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': fnum})
		format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
		font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
		red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
								'bg_color': 'red'})
		justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
		format3.set_align('center')
		font_size_8.set_align('center')
		justify.set_align('justify')
		format1.set_align('center')
		red_mark.set_align('center')

		#########TITULOS
		sheet.merge_range('A1:L1', _('Reporte de Facturas'), format1)
		datax = {}

		datax = xlines.get('data')
		option = xlines.get('option')
		groby = option.get('group_ledger')

		if groby:
			sheet.write(5, 5, _('Agrupar por'), format211)
			sheet.write(5, 6, groby, format21)
		type_of=option.get('type_of')

		if type_of:
			sheet.write(5, 1, _('Tipo'), format211)
			sheet.write(5, 2, type_of, format21)
		date_from=option.get('date_from')
		
		if date_from:
			sheet.write(3, 1, _('Fecha de Inicio'), format211)
			sheet.write(3, 2, date_from, format21)
		date_to=option.get('date_to')

		if date_to:
			sheet.write(3, 5, _('Fecha Fin'), format211)
			sheet.write(3, 6, date_to, format21)

		sheet.set_column(0, 0, 10)
		sheet.set_column(1, 1, 20)
		sheet.set_column(2, 2, 26)
		sheet.set_column(3, 3, 10)
		sheet.set_column(4, 4, 15)
		sheet.set_column(5, 5, 15)
		sheet.set_column(6,6, 10)
		sheet.set_column(7,7, 18)
		sheet.set_column(8,8, 18)
		sheet.set_column(9,9, 15)
		sheet.set_column(10,10, 18)
		sheet.set_column(11,11, 15)
		sheet.set_column(12, 12, 20)
		sheet.set_column(13, 13, 10)
		sheet.set_column(13, 13, 10)
		#
		pos=7
		option=xlines.get('option',{})
		#########"TITULOS LINEA"   	
		sheet.write(pos, 1, _('Title'), format211)	
		sheet.write(pos, 2, _('Número'), format211)
		sheet.write(pos, 3, _('PNR'), format211)
		sheet.write(pos,4, _('Contacto'), format211)
		sheet.write(pos, 5, _('Estacion'), format211)
		sheet.write(pos,6, _('Fecha'), format211)
		sheet.write(pos, 7, _('Monto Exento'), format211)
		sheet.write(pos, 8, _('Monto Isv 15'), format211)
		sheet.write(pos, 9, _('Isv 15'), format211)
		sheet.write(pos, 10, _('Monto Isv 18'), format211)
		sheet.write(pos, 11, _('Isv 18'), format211)
		sheet.write(pos, 12, _('Total'), format211)
		sheet.write(pos, 13, _('CAI'), format211)
		sheet.write(pos, 14, _('RTN'), format211)
		if option.get('life_date'):
			sheet.write(pos, 15, _('Serial'), format211)
			sheet.write(pos, 16,_('Fecha'), format211)
		pos+=1
		#CUENTAS Y LINEAS DE CUENTA
		
		for o in xlines.get('data',[]):
			if o.get('sub'):
				sheet.write(pos, 0, o.get('title_name'), format212)
				sheet.write(pos, 1, o.get('subtitle_name'), format212)
				#sheet.write_number(pos, 4,float( o.get('final',0)), format412)
				sheet.write_number(pos, 7, float(o.get('amount_0',0)), format411)
				sheet.write_number(pos, 8, float(o.get('amount_15',0)), format411)
				sheet.write_number(pos, 9, float(o.get('isv_15',0)), format411)
				sheet.write_number(pos, 10, float(o.get('amount_18',0)), format411)
				sheet.write_number(pos, 11, float(o.get('isv_18',0)), format411)
				sheet.write_number(pos, 12, float(o.get('amount_total',0)), format411)
				sheet.write(pos, 13, o.get('cai'), format21)
				sheet.write(pos, 14, o.get('rtn', ''), format21)
			else:
				#sheet.write(pos, 0, o.get('title_name'), format21)
			
				sheet.write(pos, 2, o.get('title_name'), format21)
				sheet.write(pos, 3, o.get('name',''), format21)
				sheet.write(pos, 4, o.get('subtitle_name'), format21)
				sheet.write(pos, 5, o.get('user_id') or '', format21)
				sheet.write(pos, 6, o.get('date'), format21)
				sheet.write_number(pos, 7, float(o.get('amount_0',0)), format41)
				sheet.write_number(pos, 8, float(o.get('amount_15',0)), format41)
				sheet.write_number(pos, 9, float(o.get('isv_15',0)), format41)
				sheet.write_number(pos, 10, float(o.get('amount_18',0)), format41)
				sheet.write_number(pos, 11, float(o.get('isv_18',0)), format41)
				sheet.write_number(pos, 12, float(o.get('amount_total',0)), format41)
				sheet.write(pos, 13, o.get('cai'), format21)
				sheet.write(pos, 14, o.get('rtn', ''), format21)
			pos+=1
			
			if o.get('tlines'):
				for oo in o.get('tlines'):
					
					if o.get('sub'):
						sheet.write(pos, 0, oo.get('title_name'), format212)
						sheet.write(pos, 1, oo.get('subtitle_name'), format212)
						#sheet.write_number(pos, 4,float( o.get('final',0)), format412)
						sheet.write_number(pos, 7, float(oo.get('amount_0',0)), format411)
						sheet.write_number(pos, 8, float(oo.get('amount_15',0)), format411)
						sheet.write_number(pos, 9, float(oo.get('isv_15',0)), format411)
						sheet.write_number(pos, 10, float(oo.get('amount_18',0)), format411)
						sheet.write_number(pos, 11, float(oo.get('isv_18',0)), format411)
						sheet.write_number(pos, 12, float(oo.get('amount_total',0)), format411)
						sheet.write(pos, 13, oo.get('cai'), format21)
						sheet.write(pos, 14, oo.get('rtn', ''), format21)
					else:
						#sheet.write(pos, 0, o.get('title_name'), format21)
			
						sheet.write(pos, 2, oo.get('title_name'), format21)
						sheet.write(pos, 3, oo.get('name',''), format21)
						sheet.write(pos, 4, oo.get('subtitle_name'), format21)
						sheet.write(pos, 5, oo.get('user_id') or '', format21)
						sheet.write(pos, 6, oo.get('date'), format21)
						sheet.write_number(pos, 7, float(oo.get('amount_0',0)), format41)
						sheet.write_number(pos, 8, float(oo.get('amount_15',0)), format41)
						sheet.write_number(pos, 9, float(oo.get('isv_15',0)), format41)
						sheet.write_number(pos,10, float(oo.get('amount_18',0)), format41)
						sheet.write_number(pos, 11, float(oo.get('isv_18',0)), format41)
						sheet.write_number(pos, 12, float(oo.get('amount_total',0)), format41)
						sheet.write(pos, 13, oo.get('cai'), format21)
						sheet.write(pos, 14, oo.get('rtn', ''), format21)
				
					pos+=1
					if oo.get('lines'):
						for a in oo.get('lines'):
							sheet.write(pos, 2, a.get('title_name'), format21)
							sheet.write(pos, 3, a.get('name',''), format21)
							sheet.write(pos, 4, a.get('subtitle_name'), format21)
							sheet.write(pos, 5, a.get('user_id') or '', format21)
							sheet.write(pos, 6, a.get('date'), format21)
							sheet.write_number(pos, 7, float(a.get('amount_0',0)), format41)
							sheet.write_number(pos,8, float(a.get('amount_15',0)), format41)
							sheet.write_number(pos, 9, float(a.get('isv_15',0)), format41)
							sheet.write_number(pos, 10, float(a.get('amount_18',0)), format41)
							sheet.write_number(pos, 11, float(a.get('isv_18',0)), format41)
							sheet.write_number(pos, 12, float(a.get('amount_total',0)), format41)
							sheet.write(pos, 13, a.get('cai'), format21)
							sheet.write(pos, 14, a.get('rtn', ''), format21)
							pos+=1
			
			
			if o.get('lines'):
				for a in o.get('lines'):
					sheet.write(pos, 2, a.get('title_name'), format21)
					sheet.write(pos, 3, a.get('name',''), format21)
					sheet.write(pos, 4, a.get('subtitle_name'), format21)
					sheet.write(pos, 5, a.get('user_id') or '', format21)
					sheet.write(pos, 6, a.get('date'), format21)
					sheet.write_number(pos, 7, float(a.get('amount_0',0)), format41)
					sheet.write_number(pos, 8, float(a.get('amount_15',0)), format41)
					sheet.write_number(pos, 9, float(a.get('isv_15',0)), format41)
					sheet.write_number(pos, 10, float(a.get('amount_18',0)), format41)
					sheet.write_number(pos, 11, float(a.get('isv_18',0)), format41)
					sheet.write_number(pos, 12, float(a.get('amount_total',0)), format41)
					sheet.write(pos, 13, a.get('cai'), format21)
					sheet.write(pos, 14, a.get('rtn', ''), format21)
					pos+=1
