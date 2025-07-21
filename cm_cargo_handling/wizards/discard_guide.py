# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import time

class wizard_desechar_charge(models.TransientModel):
    _name = "cm_cargo_handling.desechar_guia"
    _description = "Desechar guia"

    guia_id = fields.Many2one("cargo.bill")
    lost_reason_id = fields.Many2one("handling.lost.reason", string="Motivo")

    def apply(self):
        for record in self:
            if record.guia_id.order_id.payment_state == 'not_paid':
                move_id = record.guia_id.order_id.move_id
                if move_id.state == 'draft':
                   move_id.button_cancel()
                elif move_id.state == 'posted':
                    move_id.button_draft()
                    move_id.button_cancel()

            record.guia_id.state = "desechada"
            record.guia_id.lost_reason_id=record.lost_reason_id.id
            