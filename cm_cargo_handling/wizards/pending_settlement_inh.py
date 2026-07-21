# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class pendingSettlementReportInh(models.TransientModel):
    _inherit = "pending.settlement"

    def print_report(self):
        data = {
            'initial_date': self.initial_date,
            'final_date': self.final_date
        }
        if self.env.user.has_group("cm_cargo_handling.group_guia_cargar_admin"):
            return self.env.ref('settlement.action_pending_settlement_xlsx').report_action(self,data=data)
        else:
            return self.env.ref('cm_cargo_handling.action_pending_settlement_report_pdf').report_action(self,data=data)