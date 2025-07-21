# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class wizard_recevie_cargo_manifest(models.TransientModel):
    _name = "wizard.receive_cargo_manifest"
    _description = "Recibir manifiesto de cargo"

    observations = fields.Text(string="Observaciones")
    barcode = fields.Char(string="Codigo de barras")
    bill_landing_ids = fields.Many2many('cargo.bill', 'wizard_cargo_bill_rel_1', 'wizard_id', 'bill_id' ,string="Guias de carga")
    bill_landing_ids_hide = fields.Many2many('cargo.bill', 'wizard_cargo_bill_rel_2', 'wizard_id', 'bill_id' ,string="Guias de carga ocultas")

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
            bill_landing = self.env['cargo.bill'].search([('name','=',barcode),('state','=','sent'),('id','in',actual_ids)])
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
        for bcm in obj.cargo_bill_landing_ids:
            if bcm.bill_landing_id.id in self.bill_landing_ids_hide.ids or self.user_has_groups('cm_cargo_handling.group_cargo_manifest_validate_manifest') :
                bcm.bill_landing_id.state='received'
                bcm.bill_landing_id.cargo_manifest_id=False
                res={
                    'manifest_id':obj.id,
                    'bill_landing_id':bcm.bill_landing_id.id,
                    'observations':self.observations,
                    'type':'received'
                    }
                self.env['cargo.bill_logs'].create(res)
            else:
                raise ValidationError(_('La guia de carga %s esta aun sin escanear, no puede recibir un manifiesto de carga incompleto') %(bcm.bill_landing_id.name))
        obj.reception_observations = self.observations
        obj.state = 'received'
        obj.create_log(obj.id, self.bill_landing_ids_hide.ids, self.observations, 'received')