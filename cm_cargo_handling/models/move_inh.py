# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError

class account_invoice_inherit(models.Model):
    _inherit = "account.move"

    prestate2 = fields.Selection([("open","Abierta"),("paid","PrePagada")],string="Pre Estado",default="open",compute="compute_amount_prepago",store=True)
    invoice_additional_charge = fields.Many2one('account.move', string="id cargo")
    prepago_ids     = fields.One2many("cm.prepago", "invoice_id",string="Prepagos")
    amount_prepago  = fields.Monetary(string="Monto Prepagado",currency_field='currency_id',compute="compute_amount_prepago",store=True)
    amount_dffprepago  = fields.Monetary(string="Importe Adeudado",currency_field='currency_id',compute="compute_amount_prepago",store=True)
    from_handling = fields.Boolean(string="Desde Cargo")
    order_handling_id = fields.Many2one('sale.order.handling',string="Orden de carga")

    def print_invoice(self):
        order_id = self.env['sale.order.handling'].search([('move_id','=',self.id)])
        if order_id:
            data = {
                'order_id': order_id.id,
                'print_guides': False
                }
            return self.env.ref('cm_cargo_handling.action_invoice_guide_format').report_action(self, data=data)
        else:
            raise ValidationError("No hay orden de encomiendas ligada a esta factura")

    @api.depends("prepago_ids.state","currency_id","amount_total","rtn_name","state",'payment_state')
    def compute_amount_prepago(self):
        for record in self:
            amount_prepago = 0
            ttamount = 0.0
            for prepago in record.prepago_ids:
                if prepago.state == "posted":
                    ffprepago = prepago.currency_id._convert(prepago.amount, record.currency_id, self.env.company, prepago.payment_date, True)
                    amount_prepago += ffprepago
                    if not prepago.payment_create:
                        ttamount += ffprepago
            record.amount_prepago = amount_prepago
            record.amount_dffprepago = record.amount_residual-ttamount
            
            if record.payment_state == 'paid':
                record.prestate2 = "paid"
            else:
                if round(amount_prepago,2) >= round(record.amount_total,2):
                    record.prestate2 = "paid"
                else:
                    record.prestate2 = "open"

    def action_set_partner_pregago(self):
        for record in self.env.get("cm.prepago").search([]):
            partner_id = record.invoice_id.partner_id.id
            record.partner_id = partner_id
            if record.state == "posted":
                payment_ids = record.invoice_id.payment_ids.ids
                
                if record.payment_id:
                    payment_ids.append(record.payment_id.id)
                for payment in self.env.get("account.payment").browse(payment_ids):
                    payment.partner_id = partner_id
                    payment.partner_id_for_parents = partner_id
                for acl in self.env.get("account.move.line").search([('payment_id','in',payment_ids)]):
                    acl.partner_id = partner_id
                    acl.move_id.partner_id = partner_id

    def action_prepago(self):
        for record in self:
            val={"default_partner_id":record.partner_id.id,"default_invoice_id":record.id,"default_user_id":self.env.user.id,"default_communication":record.number}
            res={
                'type': 'ir.actions.act_window',
                'name':_("Registrar Prepago"),
                'res_model': 'cm.prepago',
                'view_type': 'form',
                'view_mode':'form',
                'context':val,
                'target': 'new',
            }

            return res
            
    def invoice_reprint(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        data = {'reprint':True}
        self.ensure_one()
        self.sent = True
        return self.env['report'].get_action(self, 'cargo_handling.report_sales_guia',data=data)

    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        data = {'reprint':False}
        self.ensure_one()
        self.sent = True
        return self.env['report'].get_action(self, 'cargo_handling.report_sales_guia',data=data)

    def action_invoice_cancel(self):
        for order in self.env['sale.order'].search([('name','=',self.origin)]):
            for line in order.order_line:
                if line.bill_lading_id:
                    if line.bill_lading_id.state in ('sent','delivered'):
                        raise ValidationError(_("No puede cancelar la factura ya que la guia %s debe estar en estado creada o recibida para poder anular la factura") %(line.bill_lading_id.name))
                    line.bill_lading_id.state='canceled'
        
        return super(account_invoice_inherit, self).action_invoice_cancel()
    
    def invoice_action_view(self):
        return {
            'type': 'ir.actions.act_window',
            'name':_("Create Invoice"),
            'res_model': 'account.move',
            'view_type': 'form',
            'view_mode':'form',
            'res_id':self.invoice_additional_charge.id,
            'target': 'current',
        }

