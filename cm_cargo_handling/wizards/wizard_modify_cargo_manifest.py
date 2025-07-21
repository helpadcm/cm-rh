# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class wizard_modify_cargo_manifest(models.TransientModel):
    _name = "wizard.modify_cargo_manifest"
    _description = "Modificar Manifiesto"

    observations = fields.Text(string="Observaciones")
    barcode = fields.Char(string="Codigo de barra")
    bill_landing_ids = fields.Many2many('cargo.bill', 'modify_cargo_bill_rel_1', 'wizard_id', 'bill_id' ,string="Guias de carga")
    bill_landing_ids_hide = fields.Many2many('cargo.bill', 'modify_cargo_bill_rel_2', 'wizard_id', 'bill_id', string="Guias de carga ocultas")

    @api.onchange('barcode')
    def onchange_barcode(self):
        obj = self.env['cargo.manifest'].browse(self.env.context.get('active_id'))
        actual_ids = []
        remove_ids = []
        if self.barcode:
            for cbl in obj.cargo_bill_landing_ids:
                actual_ids.append(cbl.bill_landing_id.id)
            
            for bl in self.bill_landing_ids:
                remove_ids.append(bl.id)

            barcode = self.barcode
            barcode = barcode.replace("'","-")
            if self.env.context.get('remove_bill_landing') == True:
                bill_landing = self.env['cargo.bill'].search([('name','=',barcode),('state','=','sent'),('id','in',actual_ids)])
            else:
                bill_landing = self.env['cargo.bill'].search([('name','=',barcode),('state','=','created'),('origin_id.airport_id','=',obj.shipping_airport.id)])
            
            if bill_landing:
                remove_ids.append(bill_landing.id)
            self.barcode = False

        self.bill_landing_ids = remove_ids
        self.bill_landing_ids_hide = remove_ids

    @api.onchange('bill_landing_ids')
    def onchange_bill_landing_ids(self):
        self.bill_landing_ids_hide = self.bill_landing_ids.ids

    def accept(self):
        obj = self.env['cargo.manifest'].browse(self.env.context.get('active_id'))
        if self.env.context.get('remove_bill_landing'):
            for bl in self.bill_landing_ids_hide:
                bl.state = 'created'
                res = {
                    'manifest_id':obj.id,
                    'bill_landing_id':bl.id,
                    'observations':self.observations,
                    'type':'removed'
                    }
                self.env['cargo.bill_logs'].create(res)


            blnds = self.env['cargo.manifest_bill_landing'].search([('bill_landing_id','in',self.bill_landing_ids_hide.ids)])
            obj.create_log(obj.id, self.bill_landing_ids_hide.ids, self.observations, 'removed')
            blnds.unlink()
        else:
            for bl in self.bill_landing_ids_hide:
                bl.state = 'sent'
                vals = {
                    'cargo_manifest_id':obj.id,
                    'bill_landing_id':bl.id,
                }
                res = {
                    'manifest_id':obj.id,
                    'bill_landing_id':bl.id,
                    'observations':self.observations,
                    'type':'added'
                    }
                self.env['cargo.bill_logs'].create(res)
                self.env['cargo.manifest_bill_landing'].create(vals)
            obj.create_log(obj.id, self.bill_landing_ids_hide.ids, self.observations, 'added')