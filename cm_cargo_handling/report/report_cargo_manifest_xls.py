from datetime import datetime
from odoo import _, models
import io
import base64
from dateutil.relativedelta import relativedelta

class cargo_manifest_xsl_Report(models.AbstractModel):
    _name = 'report.cm_cargo_handling.report_cargo_manifest_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Manifiesto de encomiendas"

    def get_data(self, data, docids):
        report_obj = self.env.get('report.cm_cargo_handling.report_cargo_manifest')
        info = report_obj.render_xls(docids, data=data)
        return info
    
    def generate_xlsx_report(self, workbook, data, lines):
        context=dict(self.env.context or {}) 
        data.update(self.env.context)
        xdata = self.get_data(data,lines)
        format41 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': 'L #,###,##0.#0'})
        format411 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': 'L #,###,##0.#0'})
        format51 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': False,'num_format': 'L #,###,##0.#0'})
        format511 = workbook.add_format({'font_size': 10, 'align': 'right', 'bold': True,'num_format': 'L #,###,##0.#0'})
        format1 = workbook.add_format({'font_size': 21, 'bottom': False, 'right': False, 'left': False, 'top': False, 'align': 'vcenter', 'bold': True})
        format12 = workbook.add_format({'font_size': 10, 'bottom': False, 'right': False, 'left': False, 'top': False, 'align': 'vcenter', 'bold': True})
        format2 = workbook.add_format({'font_size': 15,'align': 'left', 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': False})
        format212 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': False})
        format211 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format22 = workbook.add_format({'font_size': 10,'align': 'left', 'bold': False})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
										'bg_color': 'red'})
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})


        for mn in xdata.get('docs'):
            
            shipping_date=datetime.strptime(str(mn.shipping_date),"%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S")
            sheet = workbook.add_worksheet(mn.name)
            row=2
            col=0
            sheet.merge_range('E4:H5', _("MANIFIESTO DE ENCOMIENDAS"), format1)
            buf_image=io.BytesIO(base64.b64decode(self.env.user.company_id.logo_web))
            sheet.insert_image('B3',"Logo",{'image_data':buf_image})
            sheet.merge_range('B7:D7', _('Fecha: %s')%(shipping_date), format2)
            sheet.merge_range('B8:D8', _('Vuelo: %s')%(mn.flight), format2)
            sheet.merge_range('F7:G7', _('Origen: %s')%(mn.shipping_airport.ref), format2)
            sheet.merge_range('F8:G8', _('Destino: %s')%(mn.reception_airport.ref), format2)
            sheet.merge_range('H7:I7', _('No. Manifiesto: %s')%(mn.name), format2)

            row=11
            col=3


            sheet.set_column(0,0,5)
            sheet.set_column(1,1,15)
            sheet.set_column(2,2,25)
            sheet.set_column(3,4,10)
            sheet.set_column(5,5,30)
            sheet.set_column(6,6,10)
            sheet.set_column(7,7,30)


            sheet.write('A11',_('No.'),format211)
            sheet.write('B11',_('Guia'),format211)
            sheet.write('C11',_('Remitente'),format211)
            sheet.write('D11',_('Tipo'),format211)
            sheet.write('E11',_('Peso(lbs)'),format211)
            sheet.write('F11',_('Destinatario'),format211)
            sheet.write('G11',_('Destino'),format211)
            sheet.write('H11',_('Descripción'),format211)
            count=0
            for bl in mn.cargo_bill_landing_ids:
                sheet.write(row,0,count,format212)
                sheet.write(row,1,bl.bill_landing_id.name,format212)
                sheet.write(row,2,bl.bill_landing_id.sender_name,format21)
                sheet.write(row,3,bl.bill_landing_id.product_id.type_cargo.name,format212)
                sheet.write(row,4,bl.bill_landing_id.weight,format21)
                sheet.write(row,5,bl.bill_landing_id.receiver_name,format21)
                sheet.write(row,6,bl.bill_landing_id.destination_id.ref,format212)
                sheet.write(row,7,bl.bill_landing_id.observations or '',format21)
                count+=1
                row+=1
            sheet.write(row,2,_('Totales'),format211)
            sheet.write(row,4,mn.total_weight,format211)
            row+=2
            sheet.write(row,1,_('Creado por: '),format12)
            sheet.write(row,2,mn.create_uid.name+" ---------------------------------------",format12)
            sheet.write(row,6,_('Impreso: '),format12)
            sheet.write(row,7,(datetime.today()-relativedelta(hours=6)).strftime("%d-%m-%Y %H:%M:%S"),format12)