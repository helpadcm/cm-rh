# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class wizard_desechar_charge(models.TransientModel):
    _name = "cm_cargo_handling.desechar_guia"
    _description = "Desechar guia"

    guia_ids = fields.Many2many("cargo.bill")
    lost_reason_id = fields.Many2one("handling.lost.reason", string="Motivo")

    def apply(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        for record in self:
            for guide in record.guia_ids:
                if guide.state not in ['created','received']:
                    raise ValidationError("Solo se pueden desechar guias en estado creada y recibida")

                if guide.order_id.payment_state == 'not_paid':
                    move_id = guide.order_id.move_id
                    if move_id.state == 'draft':
                        move_id.button_cancel()
                    elif move_id.state == 'posted':
                        move_id.button_draft()
                        move_id.button_cancel()

                guide.state = "desechada"
                guide.lost_reason_id=record.lost_reason_id.id
                guide.create_log('cancelled', 'Cancelada')
            
        if active_model == 'sale.order.handling':
            order_id = self.env[active_model].browse(active_id)
            if order_id.move_id:
                if order_id.move_id.state == 'draft':
                    order_id.move_id.button_cancel()
                
                if order_id.move_id.state == 'posted' and order_id.move_id.payment_state == 'not_paid':
                    order_id.move_id.button_draft()
                    order_id.move_id.button_cancel()

                    if order_id.move_id.prepago_ids:
                        for prep in order_id.move_id.prepago_ids:
                            prep.action_cancel()

                if order_id.move_id.payment_state in ['partial','paid','in_payment']:
                    raise ValidationError("La factura ya cuenta con un pago, antes de desechar o cancelar la orden debe desconciliar los pagos")

            order_id.state = 'canceled'