# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError

class CmPrepago(models.Model):
    _name = "cm.prepago"
    _description = "Prepagos de factura"
    _order="id desc"

    state = fields.Selection([('draft', 'Borrador'), ('posted', 'Validado'), ('cancel', 'Cancelada')], readonly=True, default='draft', copy=False, string="Status")
    name        = fields.Char(string="Número")
    user_id     = fields.Many2one("res.users",string="Usuario")
    journal_id  = fields.Many2one("account.journal",string="Diario", required=True, domain=[('type', 'in', ('bank', 'cash'))])
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', required=True, default=lambda self: self.env.user.company_id.currency_id)
    partner_id = fields.Many2one('res.partner', string='Cliente')
    invoice_id  = fields.Many2one("account.move",string="Factura")
    cargo_handling_id = fields.Many2one("sale.order.handling",string="Cargo Handling")
    payment_id  = fields.Many2one("account.payment",string="Pago")
    amount      = fields.Monetary(string="Importe", required=True)
    payment_date= fields.Date(string="Fecha de Pago",default=fields.Date.context_today, required=True, copy=False)
    communication= fields.Char(string="Concepto")
    type = fields.Selection([('bank','Bank'),('cash','Cash')],'type')
    request_card_data = fields.Boolean(string='Request Data')
    nro_auto = fields.Char(string='Nro AUTO')
    card_digits = fields.Char(string='Card Digits')
    payment_create = fields.Boolean(string="Pago Creado")
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], default="inbound",string='Tipo de Pago', required=True)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method Type')
    payment_method_code = fields.Char(related='payment_method_id.code', help="Technical field used to adapt the interface to the payment type selected.", readonly=True)
    payment_difference = fields.Monetary(compute='_compute_payment_difference',string="Diferencia", readonly=True)
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')],default="customer")
    hide_payment_method = fields.Boolean(compute='_compute_hide_payment_method', help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")
    payment_difference_handling = fields.Selection([('open', 'Mantener Abierta'), ('reconcile', 'Marcar Como Pagada')], default='open', string="Diferencia del Pago", copy=False)
    amount_usd = fields.Float(string="Importe USD",compute="_compute_amount_currency")
    amount_hnl = fields.Float(string="Importe HNL",compute="_compute_amount_currency")
    guia_ids = fields.Char(string="Guías",compute="_compute_guia")
    rtn = fields.Char(string="RTN")
    client_name = fields.Char(string="Nombre del cliente")

    @api.depends("cargo_handling_id")
    def _compute_guia(self):
        for record in self:
            number_guides = ""
            if record.cargo_handling_id:
                guides_ids = self.env['cargo.bill'].search([('order_id','=',record.cargo_handling_id.id)])
                if guides_ids:
                    number_guides = ', '.join([guide.name for guide in set(guides_ids)])
            record.guia_ids = number_guides

    @api.depends("currency_id", "amount", "state")
    def _compute_amount_currency(self):
        for record in self:
            base_USD = self.env.ref('base.USD')
            base_HNL = self.env.ref('base.HNL')
            amount_usd = 0.0
            amount_hnl = 0.0
            if record.state == "posted":
                if record.currency_id:
                    if record.currency_id.id == base_HNL.id:
                        amount_hnl += record.amount
                    if record.currency_id.id == base_USD.id:
                        amount_usd += record.amount
                else:
                    amount_hnl += record.amount
            record.amount_usd = amount_usd
            record.amount_hnl = amount_hnl


    @api.model
    def cron_sent_pays(self):
        domain=[('state','=','posted'),("payment_create","=",False)]
        pay_ids = self.search(domain)
        for pay in pay_ids:
            pay.post_to_pay()
        
        domain = [('state','!=','posted'),("payment_create","=",False)]
        pay_ids = self.search(domain)
        for pay in pay_ids:
            pay.cancel_to_pay()

    def post(self):
        active_model = self.env.context.get('active_model')
        for record in self:
            if record.invoice_id.prestate2 == "paid":
                raise ValidationError("La Factura ya fue Pagada")

            if record.cargo_handling_id:
                if record.cargo_handling_id.modality == 'counted' and not record.cargo_handling_id.move_id:
                    move_id = record.cargo_handling_id.create_invoices()
                    record.invoice_id = move_id.id

                if active_model != 'cargo.bill':
                    record.cargo_handling_id.with_context({"create": True}).create_guides()
            record.state="posted"

    def cancel_to_pay(self):
        for cash in self:
            if cash.state!="posted" and not cash.payment_create:
                cash.payment_create=True

    def post_to_pay(self):
        for cash in self:
            if cash.state == "posted" and not cash.payment_create:
                cash.payment_create=True
                if cash.invoice_id.state != "posted" or cash.invoice_id.payment_state == 'paid':
                    continue

                vals={
                    'date': cash.payment_date,
                    #'state':cash.state,
                    'reconciled_invoice_ids': [(6,0,[cash.invoice_id.id])],
                    'currency_id': cash.currency_id.id,
                    #'obs':cash.obs,
                    'journal_id': cash.journal_id.id,
                    'amount': cash.amount,
                    'communication': cash.communication,
                    'ref': cash.communication,
                    'company_id': cash.company_id.id,
                    'user_id': cash.user_id.id,
                    'partner_id': cash.partner_id.id,
                    'partner_id_for_parents': cash.partner_id.id,
                    'partner_type': cash.partner_type,
                    'payment_type': cash.payment_type,
                    'nro_auto': cash.nro_auto,
                    'card_digits': cash.card_digits,
                    # 'payment_method_id': cash.payment_method_id.id,
                }
                if cash.rtn:
                    cash.invoice_id.rtn_name = cash.rtn
                if cash.client_name:
                    cash.invoice_id.partner_name = cash.client_name
                    
                pay_id = self.env.get("account.payment").create(vals)
                pay_id.action_post()
                # Obtener las líneas de débito y crédito del pago y la factura
                payment_lines = pay_id.move_id.line_ids.filtered(lambda line: line.account_id.reconcile)
                invoice_lines = cash.invoice_id.line_ids.filtered(lambda line: line.account_id.reconcile)

                # Conciliar las líneas. El método `reconcile()` toma un conjunto de líneas y las concilia.
                (payment_lines | invoice_lines).reconcile()
                cash.payment_id = pay_id.id

    def action_draft(self):
        for record in self:
            record.state="draft"

    def action_cancel(self):
        for record in self:
            if not record.payment_create:
                record.state="cancel"
            else:
                raise ValidationError("El Pago de la factura ya fue procesado")

    @api.model_create_multi
    def create(self, vals_list):
        records = super(CmPrepago, self).create(vals_list)
        for record in records:
            record.name = "PP{:08}".format(record.id)
            record.invoice_id.from_handling = True
            if record.rtn:
                record.invoice_id.rtn_name = record.rtn
            if record.client_name:
                record.invoice_id.partner_name = record.client_name
        return records


    # @api.onchange('payment_type')
    # def _onchange_payment_type(self):
    #     if not self.invoice_id:
    #         # Set default partner type for the payment type
    #         if self.payment_type == 'inbound':
    #             self.partner_type = 'customer'
    #         elif self.payment_type == 'outbound':
    #             self.partner_type = 'supplier'
    #         else:
    #             self.partner_type = False
    #     # Set payment method domain
    #     # res = self._onchange_journal()
    #     if not res.get('domain', {}):
    #         res['domain'] = {}
    #     res['domain']['journal_id'] = self.payment_type == 'inbound' and [('at_least_one_inbound', '=', True)] or self.payment_type == 'outbound' and [('at_least_one_outbound', '=', True)] or []
    #     res['domain']['journal_id'].append(('type', 'in', ('bank', 'cash')))
    #     res['domain']['journal_id'].append(('valid_for_payments','=',True))
    #     res['domain']['journal_id'].append(('user_ids','=',self.user_id.id))
    #     return res

    
    @api.depends('payment_type', 'journal_id')
    def _compute_hide_payment_method(self):
        if not self.journal_id:
            self.hide_payment_method = True
            return
        journal_payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_line_ids or self.journal_id.outbound_payment_method_line_ids
        self.hide_payment_method = len(journal_payment_methods) == 1 and journal_payment_methods[0].code == 'manual'

    
    @api.constrains('amount')
    def _check_amount(self):
        if not self.amount > 0.0:
            raise ValidationError(_('El Pago debe ser Positivo'))

    
    @api.depends('invoice_id', 'amount', 'payment_date', 'currency_id', 'journal_id')
    def _compute_payment_difference(self):
        if not self.invoice_id:
            return
        if self.invoice_id.move_type in ['in_invoice', 'out_refund']:
            self.payment_difference = self.amount - self._compute_total_invoices_amount()
        else:
            self.payment_difference = self._compute_total_invoices_amount() - self.amount

    def _compute_total_invoices_amount(self):
        """ Compute the sum of the residual of invoices, expressed in the payment currency """
        payment_currency = self.journal_id.currency_id or self.journal_id.company_id.currency_id or self.env.user.company_id.currency_id
        invoices = [self.invoice_id]

        if all(inv.currency_id == payment_currency for inv in invoices):
            total = self.invoice_id.amount_total#sum(invoices.mapped(''))
        else:
            total = 0
            for inv in invoices:
                if inv.company_currency_id != payment_currency:
                    total += inv.company_currency_id._convert(inv.amount_total, payment_currency, self.env.company, self.payment_date, True)
                else:
                    total += inv.amount_total_signed
        for inv in invoices:
            for prepago in inv.prepago_ids:
                if prepago.state == "posted" and not prepago.payment_create:
                    total -= prepago.currency_id._convert(prepago.amount, payment_currency, self.env.company, prepago.payment_date, True)
        
        return abs(total)
    
    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            self.type = self.journal_id.type
            self.request_card_data = self.journal_id.request_card_data
            self.currency_id = self.journal_id.currency_id or self.company_id.currency_id
        #     # Set default payment method (we consider the first to be the default one)
        #     payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_line_ids or self.journal_id.outbound_payment_method_line_ids
        #     self.payment_method_id = payment_methods and payment_methods[0].id or False
            self.amount = self._compute_total_invoices_amount()
        #     # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
        #     payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'
        #     print ("33333333333333333333333333333333333333333333333333333333333")
        #     print (payment_methods)
        #     return {'domain': {'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods.ids)]}}
        # return {}
