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
    group_invoice_id = fields.Many2one('cargo.invoice.group_guides',string="Facturacion de guias")

    def print_invoice(self):
        order_id = self.env['sale.order.handling'].search([('move_id','=',self.id)])
        if order_id:
            if self.group_invoice_id:
                data = {
                    'order_id': order_id,
                    'group_invoice_id': self.group_invoice_id.id,
                    'print_guides': False
                }
            else:
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

    def _post(self, soft=True):
        res = super(account_invoice_inherit, self)._post(soft=False)
        for rec in res:
            if rec.move_type == 'out_invoice':
                if rec.partner_id.credit_ticket or rec.partner_id.modality == 'credit':
                    if rec.partner_id.available_credit < rec.amount_residual:
                        raise ValidationError(f"""El cliente {rec.partner_id.name} no tiene credito disponible. Su saldo actual es de {rec.partner_id.available_credit}""")
                    rec.partner_id.available_credit -= rec.amount_residual
        return res

    def button_draft(self):
        res = super(account_invoice_inherit, self).button_draft()
        if self.move_type == 'out_invoice':
            if self.partner_id.credit_ticket or self.partner_id.modality == 'credit':
                self.partner_id.available_credit += self.amount_residual
        return res

class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            invoice_line = rec.debit_move_id.move_id
            payment_line = rec.credit_move_id.move_id

            invoice = invoice_line if invoice_line.move_type == 'out_invoice' else payment_line
            if not invoice or invoice.move_type != 'out_invoice':
                continue

            partner = invoice.partner_id
            if partner.credit_ticket or partner.modality == 'credit':
                rline = invoice.line_ids.filtered(lambda l: l.account_id.reconcile)

                for line in rline:
                    ratio = abs(rec.amount) / abs(line.balance)
                    paid_usd = abs(line.amount_currency) * ratio
                    partner.available_credit += round(paid_usd,2)

        return records

    def unlink(self):
        for rec in self:
            invoice_line = rec.debit_move_id.move_id
            payment_line = rec.credit_move_id.move_id

            invoice = invoice_line if invoice_line.move_type == 'out_invoice' else payment_line
            if not invoice or invoice.move_type != 'out_invoice':
                continue

            partner = invoice.partner_id
            if partner.credit_ticket or partner.modality == 'credit':
                rline = invoice.line_ids.filtered(lambda l: l.account_id.reconcile)

                for line in rline:
                    ratio = abs(rec.amount) / abs(line.balance)
                    paid_usd = abs(line.amount_currency) * ratio
                    partner.available_credit -= round(paid_usd,2)

        return super().unlink()

class moveLineinherit(models.Model):
    _inherit = "account.move.line"

    def add_budget_account(self):
        self.env.cr.execute("""
            SELECT account_budget_account_id
            FROM account_account_account_budget_account_rel
            WHERE account_account_id = %s
        """, (self.account_id.id,))
        rows = self.env.cr.fetchall()

        budget_account_id = False
        if len(rows) > 0:
            try:
                budget_account_id = rows[0][0]
            except:
                budget_account_id = False

        if budget_account_id:
            source_id = self.env['crossovered.source_expenditure'].search([('code','=','VT')])
            process_id = self.env['crossovered.activity'].search([('code','=','PP06-COM')])
            self.write({
                'analytic_account_id': budget_account_id,
                'activity_id': process_id.id,
                'source_id': source_id.id
            })
            self.create_budget_lines()