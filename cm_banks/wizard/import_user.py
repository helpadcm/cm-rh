# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from babel.dates import format_date
import calendar
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from openpyxl import load_workbook
import base64
from io import BytesIO

class import_user_wizard(models.TransientModel):
    _name = 'import_payment_user_wizard'
    _description = "Importar usuario de pago"
	
    format_doc = fields.Binary(string="Formato de importacion")
    doc_name = fields.Char(string="Nombre de Documento")

    def import_document(self):
        file_content = base64.b64decode(self.format_doc)

        wb = load_workbook(filename=BytesIO(file_content))
        ws = wb.active  # toma la primera hoja

        # Iterar por filas
        line_number = 2
        for row in ws.iter_rows(min_row=2, values_only=True):  # min_row=2 para saltar encabezados
            payment_id = row[1]
            user_id = row[2]
            if payment_id and user_id:
                sql = f"""UPDATE account_payment SET user_id = {user_id} WHERE id = {payment_id}"""
                self.env.cr.execute(sql)