import base64
from io import BytesIO
from collections import defaultdict
from odoo import models, _

class VentasClienteXlsx(models.AbstractModel):
    _name = 'report.reporte_ventas_clientes.report_ventas_cliente_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Reporte XLSX de Ventas Agrupado por Cliente"

    def _get_report_filename(self, objs):
        if objs and len(objs) == 1:
            wizard = objs[0]
            start_str = wizard.date_start.strftime('%d-%m-%Y') if wizard.date_start else ''
            end_str = wizard.date_end.strftime('%d-%m-%Y') if wizard.date_end else ''
            return f"Ventas por Clientes {start_str} al {end_str}"
        return "Ventas por Clientes"

    def generate_xlsx_report(self, workbook, data, wizards):
        for wizard in wizards:
            grouped_data, grand_totals = self.get_data(wizard)
            sheet = workbook.add_worksheet('Clientes con Descuento')

            # --- ESTILOS Y FORMATOS DE CELDAS ---
            title_format = workbook.add_format({
                'font_size': 13, 
                'align': 'center', 
                'valign': 'vcenter', 
                'bold': True
            })

            date_header_format = workbook.add_format({
                'font_size': 10,
                'align': 'center',
                'valign': 'vcenter',
                'bold': True
            })
            
            client_header_format = workbook.add_format({
                'font_size': 11, 
                'align': 'left', 
                'valign': 'vcenter', 
                'bold': True, 
                'bg_color': '#E0E0E0', 
                'border': 1
            })
            
            header_format = workbook.add_format({
                'font_size': 10, 
                'align': 'center', 
                'valign': 'vcenter', 
                'bold': True, 
                'bg_color': '#424242', 
                'font_color': '#FFFFFF', 
                'border': 1
            })
            
            data_format = workbook.add_format({
                'font_size': 10, 
                'align': 'left', 
                'valign': 'vcenter', 
                'border': 1
            })
            data_center_format = workbook.add_format({
                'font_size': 10, 
                'align': 'center', 
                'valign': 'vcenter', 
                'border': 1
            })
            num_format = workbook.add_format({
                'font_size': 10, 
                'align': 'right', 
                'valign': 'vcenter', 
                'border': 1, 
                'num_format': '#,##0.00'
            })
            usd_format = workbook.add_format({
                'font_size': 10, 
                'align': 'right', 
                'valign': 'vcenter', 
                'border': 1, 
                'num_format': '$#,##0.00'
            })
            lps_format = workbook.add_format({
                'font_size': 10, 
                'align': 'right', 
                'valign': 'vcenter', 
                'border': 1, 
                'num_format': 'L #,##0.00'
            })
            
            # Formato sin borde para la zona combinada A-F en subtotales
            subtotal_empty_format = workbook.add_format({
                'border': 0
            })

            subtotal_usd_format = workbook.add_format({
                'font_size': 10, 
                'align': 'right', 
                'valign': 'vcenter', 
                'bold': True, 
                'border': 1, 
                'bg_color': '#EEEEEE', 
                'num_format': '$#,##0.00'
            })
            subtotal_lps_format = workbook.add_format({
                'font_size': 10, 
                'align': 'right', 
                'valign': 'vcenter', 
                'bold': True, 
                'border': 1, 
                'bg_color': '#EEEEEE', 
                'num_format': 'L #,##0.00'
            })

            # --- ESTILOS PARA TOTAL GENERAL (RESUMEN) ---
            grand_total_header_format = workbook.add_format({
                'font_size': 11, 
                'align': 'center', 
                'valign': 'vcenter', 
                'bold': True, 
                'bg_color': '#2E4053', 
                'font_color': '#FFFFFF', 
                'border': 1
            })

            grand_total_label_format = workbook.add_format({
                'font_size': 10, 
                'align': 'left', 
                'valign': 'vcenter', 
                'bold': True, 
                'bg_color': '#D5D8DC', 
                'border': 1
            })

            grand_total_usd_format = workbook.add_format({
                'font_size': 11, 
                'align': 'right', 
                'valign': 'vcenter', 
                'bold': True, 
                'border': 1, 
                'bg_color': '#F2F4F4', 
                'num_format': '$#,##0.00'
            })

            grand_total_lps_format = workbook.add_format({
                'font_size': 11, 
                'align': 'right', 
                'valign': 'vcenter', 
                'bold': True, 
                'border': 1, 
                'bg_color': '#F2F4F4', 
                'num_format': 'L #,##0.00'
            })

            # --- CONFIGURACIÓN DE ANCHO DE COLUMNAS (A HASTA H) ---
            sheet.set_column('A:A', 6)   # N°
            sheet.set_column('B:C', 18)  # # Guía y Fecha
            sheet.set_column('D:D', 16)  # Modalidad
            sheet.set_column('E:E', 12)  # Peso
            sheet.set_column('F:F', 25)  # Descuento
            sheet.set_column('G:H', 18)  # Total USD y Total Lps

            # --- LOGO CORPORATIVO ---
            if self.env.user.company_id.logo:
                image_data = BytesIO(base64.b64decode(self.env.user.company_id.logo))
                sheet.insert_image('A1', 'logo', {
                    'image_data': image_data, 
                    'x_scale': 0.08, 
                    'y_scale': 0.08, 
                    'x_offset': 10, 
                    'y_offset': 5
                })

            # --- ENCABEZADO PRINCIPAL Y FECHAS CENTRADAS (A1:H1) ---
            sheet.merge_range('A1:H1', _('CLIENTES CON DESCUENTO'), title_format)

            date_start_str = wizard.date_start.strftime('%d/%m/%Y') if wizard.date_start else ''
            date_end_str = wizard.date_end.strftime('%d/%m/%Y') if wizard.date_end else ''

            sheet.merge_range('B2:C2', _('Desde: %s') % date_start_str, date_header_format)
            sheet.merge_range('F2:G2', _('Al: %s') % date_end_str, date_header_format)

            pos = 4

            # --- IMPRESIÓN DE DATOS AGRUPADOS POR CLIENTE ---
            for client_name, client_info in grouped_data.items():
                sheet.merge_range(pos, 0, pos, 7, _('Cliente: %s') % client_name, client_header_format)
                pos += 1

                headers = ['N°', '# de Guía', 'Fecha', 'Modalidad', 'Peso', 'Descuento', 'Total USD', 'Total Lps']
                for col, h in enumerate(headers):
                    sheet.write(pos, col, h, header_format)
                pos += 1

                for idx, row in enumerate(client_info['orders'], start=1):
                    sheet.write_number(pos, 0, idx, data_center_format)
                    sheet.write(pos, 1, row.get('number'), data_format)
                    sheet.write(pos, 2, row.get('date'), data_center_format)
                    sheet.write(pos, 3, row.get('modality'), data_center_format)
                    sheet.write_number(pos, 4, row.get('weight'), num_format)
                    sheet.write(pos, 5, row.get('discount_name'), data_format)
                    sheet.write_number(pos, 6, row.get('total_usd'), usd_format)
                    sheet.write_number(pos, 7, row.get('total_lps'), lps_format)
                    pos += 1

                # SUBTOTALES POR CLIENTE (Sin bordes de A a F)
                sheet.merge_range(pos, 0, pos, 5, '', subtotal_empty_format)
                sheet.write_number(pos, 6, client_info['subtotal_usd'], subtotal_usd_format)
                sheet.write_number(pos, 7, client_info['subtotal_lps'], subtotal_lps_format)
                pos += 2

            # --- RESUMEN DE TOTAL GENERAL ---
            pos += 1

            sheet.merge_range(pos, 0, pos, 3, _('RESUMEN - TOTAL GENERAL'), grand_total_header_format)
            pos += 1

            sheet.merge_range(pos, 0, pos, 1, _('Moneda'), grand_total_label_format)
            sheet.merge_range(pos, 2, pos, 3, _('Monto Total'), grand_total_label_format)
            pos += 1

            sheet.merge_range(pos, 0, pos, 1, _('Total USD ($)'), grand_total_label_format)
            sheet.merge_range(pos, 2, pos, 3, grand_totals['usd'], grand_total_usd_format)
            pos += 1

            sheet.merge_range(pos, 0, pos, 1, _('Total LPS (L)'), grand_total_label_format)
            sheet.merge_range(pos, 2, pos, 3, grand_totals['lps'], grand_total_lps_format)

    def get_data(self, wizard):
        # 1. DOMAIN EN SQL: Mantiene el filtro de estado 'invoiced' (Finalizado) y discount_id
        domain = [
            ('create_date', '>=', wizard.date_start),
            ('create_date', '<=', wizard.date_end),
            ('state', '=', 'invoiced'),
            ('partner_id.default_client', '=', False),
            ('partner_id.cargo_client', '=', True),
            ('discount_id', '!=', False),
        ]

        if getattr(wizard, 'partner_ids', False):
            domain.append(('partner_id', 'in', wizard.partner_ids.ids))

        # Filtro opcional por modalidad
        selected_modality = getattr(wizard, 'modality', 'all')
        if selected_modality and selected_modality != 'all':
            domain.append(('modality', '=', selected_modality))

        orders = self.env['sale.order.handling'].search(domain)

        grouped_data = defaultdict(lambda: {
            'orders': [],
            'subtotal_usd': 0.0,
            'subtotal_lps': 0.0
        })

        grand_totals = {'usd': 0.0, 'lps': 0.0}
        excluded_discount_codes = ['G10', 'COMAIL', 'GUIA #10']

        for order in orders:
            partner = order.partner_id
            
            if not partner:
                continue

            # Validar cliente que no sea por defecto y sea de carga
            if getattr(partner, 'default_client', False) or not getattr(partner, 'cargo_client', False):
                continue

            # Validar estado 'invoiced'
            state_raw = (getattr(order, 'state', '') or '').lower().strip()
            if state_raw != 'invoiced':
                continue

            # Validación de modalidad en Python
            order_modality_raw = getattr(order, 'modality', '') or ''
            if selected_modality and selected_modality != 'all' and order_modality_raw != selected_modality:
                continue

            # Validar descuento directo en la guía
            discount_obj = order.discount_id
            if not discount_obj:
                continue

            discount_code = (getattr(discount_obj, 'code', '') or getattr(discount_obj, 'name', '') or '').strip().upper()
            discount_name = discount_obj.name or discount_obj.display_name or ''

            # Exclusión de tarifas o códigos no promocionales
            if any(ex in discount_code for ex in excluded_discount_codes) or any(ex in discount_name.upper() for ex in excluded_discount_codes):
                continue

            # Mapeo de la etiqueta visible de la Modalidad
            modality_label = ''
            if hasattr(order._fields.get('modality'), 'selection'):
                modality_dict = dict(order._fields['modality'].selection)
                modality_label = modality_dict.get(order_modality_raw, order_modality_raw)
            else:
                modality_label = order_modality_raw

            weight_val = getattr(order, 'weight', 0.0) or getattr(order, 'peso', 0.0) or getattr(order, 'total_weight', 0.0) or 0.0
            total_usd_val = getattr(order, 'amount_total', 0.0)
            total_lps_val = getattr(order, 'amount_total_lps', 0.0)

            client_name = partner.name or 'Sin Nombre'

            order_data = {
                'number': getattr(order, 'name', '') or 'Borrador',
                'date': order.create_date.strftime('%d/%m/%Y') if order.create_date else '',
                'modality': modality_label,
                'weight': weight_val,
                'discount_name': discount_name,
                'total_usd': total_usd_val,
                'total_lps': total_lps_val,
            }

            grouped_data[client_name]['orders'].append(order_data)
            grouped_data[client_name]['subtotal_usd'] += total_usd_val
            grouped_data[client_name]['subtotal_lps'] += total_lps_val

            grand_totals['usd'] += total_usd_val
            grand_totals['lps'] += total_lps_val

        return grouped_data, grand_totals