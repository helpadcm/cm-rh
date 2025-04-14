# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

class saleOrderInherit(models.Model):
    _inherit = 'sale.order'

    purchase_order_exempt = fields.Char(string="N° Orden de compra exenta")
    record_exonerated = fields.Char(string="N° Constancia de registro exonerado")
    sag_record = fields.Char(string="N° Registro de la SAG")

    # def _prepare_invoice(self):
    #     res = super(saleOrderInherit,self)._prepare_invoice()
    #     res.update({
    #         'purchase_order_exempt':self.purchase_order_exempt,
    #         'record_exonerated':self.record_exonerated,
    #         'sag_record':self.sag_record
    #     })
    #     return res