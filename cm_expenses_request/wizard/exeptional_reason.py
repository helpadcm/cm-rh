from odoo import models, fields, _, api
from datetime import datetime, timedelta, time
from odoo.exceptions import ValidationError


class expenseExeptionReason(models.TransientModel):
    _name = "expense.exeption.reason"
    _description = "Agregar motivo de excepcion"

    exeption_id = fields.Many2one('expense.exceptional.reason',string='Motivo de Excepcion')
    description = fields.Text(string="Motivo")

    def request_exeption(self):
        context = self.env.context
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        req_id = self.env[active_model].search([('id','in',active_ids)])

        for line in req_id.expenses_ids:
            if line.nb_attachment == 0:
                raise ValidationError(f"""Debe agregar comprobantes de sus gastos, el gasto {line.name} no tiene adjuntos. Para agregarlo ingrese a la linea del gasto descrito y suba el comprobante desde el boton 'Adjuntar recibo'""")

        req_id.write({'exeption_id':self.exeption_id.id,'description':self.description})
        
        next_state = 'exception'
        if self.exeption_id.skip_exception:
            next_state = 'pending'
            req_id.refund_state = 'na'
            
        req_id.with_context({'state':next_state}).change_state()