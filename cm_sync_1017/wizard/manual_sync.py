# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

select = [('mchecks','Pagos Miscelaneos'), ('db_cr','Debitos y Creditos'), ('deposits','Depositos'), ('supplier_inv','Facturas Proveedor'), ('customer_inv','Facturas de Cliente'), ('moves','Asientos Contables'), ('rate','Tasa de Cambio')]

class manualSync(models.TransientModel):
    _name = 'manual.synchronization'
    _description = "Sincronizacion manual"

    model_selection = fields.Selection(select, string="Modelo",default="mchecks")
    type_selection = fields.Selection([('test','Pruebas'),('production','Produccion')], string="Para")
    start_date = fields.Date(string="Fecha Inicial")
    end_date = fields.Date(string="Fecha Final")
    limit = fields.Integer(string="Limite")


    def synchronization_manual(self):
        if self.model_selection == 'mchecks':
            model = 'mcheck.mcheck'
            self.env[model].with_context({'start_date': self.start_date, 'end_date': self.end_date, 'opt': self.type_selection}).sync_mchecks(self.type_selection)
        elif self.model_selection == 'db_cr':
            model = 'debit.credit'
            self.env[model].with_context({'start_date': self.start_date, 'end_date': self.end_date, 'opt': self.type_selection}).sync_debit_credit(self.type_selection)
        elif self.model_selection == 'deposits':
            model = 'banks.deposit'
            self.env[model].with_context({'start_date': self.start_date, 'end_date': self.end_date, 'opt': self.type_selection}).sync_deposits(self.type_selection)
        elif self.model_selection in ['supplier_inv','customer_inv','moves']:
            model = 'account.move'
            move_type = 'customer'
            if self.model_selection == 'supplier_inv':
                move_type = 'supplier'
                
            add_context = {
                'start_date': self.start_date, 
                'end_date': self.end_date, 
                'opt': self.type_selection,
                'limit': self.limit,
                'type': move_type
            }
            self.env[model].with_context(add_context).sync_invoices(self.type_selection)
        else:
            model = 'res.currency.rate'
            self.env[model].with_context({'start_date': self.start_date, 'opt': self.type_selection}).sync_rate(self.type_selection)
        return True