# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _

class wizard_cancel_cargo_manifest(models.TransientModel): 
    _name = "wizard.cancel_cargo_manifest"   
    _description = "Cancelar Manifiesto"

    observations = fields.Text(string="Observaciones")
   
    def accept(self):
        obj=self.env['cargo.manifest'].browse(self.env.context.get('active_id'))
        for bl in obj.cargo_bill_landing_ids:
            bl.bill_landing_id.state='created'
            bl.bill_landing_id.cargo_manifest_id=False  
            res = {
                'manifest_id':obj.id,
                'bill_landing_id':bl.bill_landing_id.id,
                'observations':self.observations,
                'type':'cancelled'
                }
            self.env['cargo.bill_logs'].create(res)
        obj.state = 'cancelled'          
        obj.create_log(obj.id,obj.cargo_bill_landing_ids.mapped('bill_landing_id').ids, self.observations, 'cancelled')