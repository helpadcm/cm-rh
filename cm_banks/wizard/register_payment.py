# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class account_payment_inherit_wizard(models.TransientModel):
    _inherit= "account.payment.register"

    next_number = fields.Char(string='Siguiente Numero', help='El numero siguiente del cheque o transferencia', default="Borrador")
    writeoff_amount = fields.Float(string="Diferencia", compute='_compute_writeoff_amount')
    write_off_lines = fields.One2many('account.payment.writeoffline.wizard', 'register_id', string="Write off lines")
    analytic_account_id	=	fields.Many2one('account.analytic.account',string="Cuenta Analitica")
    invoice_compute = fields.Many2many('account.move.line', string="move lines")
    payment_line_ids = fields.One2many('account.payment.line.register', 'register_id',string="Lineas de pago")
    pay_method_type= fields.Selection([
                ('check','Check'),
                ('transference','Transference'),
                ('otros','Otros')], string='Tipo de transaccion')

    @api.model
    def _get_batch_communication(self, batch_result):
        if self.payment_type == 'outbound':
            labels = set(line.move_id.ref or line.move_id.name for line in batch_result['lines'])
        else:
            labels = set(line.move_id.payment_reference or line.name or line.move_id.ref or line.move_id.name for line in batch_result['lines'])
        return ', '.join(sorted(labels))

    @api.model
    def default_get(self, fields):
        rec = super(account_payment_inherit_wizard, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        # invoices = self.env[active_model].browse(active_ids)
        #domain=[('move_id','in',invoices.ids),('full_reconcile_id','=',False),('partner_id','=',rec.get('partner_id'))]
        # if invoices[0].move_type == 'in_invoice':
        #     type_account = 'liability_payable'
        # if invoices[0].move_type == 'out_invoice':
        #     type_account = 'asset_receivable'
        # move_line_obj = invoices.filtered(lambda line: line.reconciled == False and line.account_id.account_type == type_account)
        # pay_line_ids = []
        # for ml in move_line_obj:
        #     vals = {
        #         'move_line_id': ml.id,
        #         'account_id': ml.account_id.id,
        #         'amount_original': ml.move_id.amount_total,
        #         'currency_id': ml.currency_id.id,
        #         'date_original': ml.date,
        #         'date_due': ml.date_maturity,
        #         'amount_unreconcilied': ml.move_id.amount_residual,
        #         'amount': ml.move_id.amount_residual,
        #         'reconcile': True
        #     }
        #     pay_line_ids.append((0, 0, vals))
        rec.update({
            'invoice_compute': [(6, 0, active_ids)],
            # 'payment_line_ids': pay_line_ids
        })
        return rec

    @api.onchange('journal_id', 'pay_method_type')
    def onchange_journal(self):
        if self.journal_id:
            # self.recalc()
            if self.partner_type == 'customer':
                if self.journal_id.sequence_id:
                    sequence_id = self.journal_id.sequence_id
                    # next_number = sequence_id.get_next_char(sequence_id.number_next_actual)
                    date = self.payment_date or fields.Date.context_today(sequence_id)
                    number_next = None

                    # Buscar si la secuencia usa rango de fechas
                    if sequence_id.use_date_range:
                        date_range = sequence_id.date_range_ids.filtered(
                            lambda r: r.date_from <= date <= r.date_to
                        )
                        if date_range:
                            number_next = date_range.number_next_actual

                    # Si no usa rango de fechas o no encontró rango válido
                    if not number_next:
                        number_next = sequence_id.number_next_actual

                    # Devuelve el número formateado
                    next_number = sequence_id.get_next_char(number_next)
                    self.next_number = next_number
            else:
                if self.journal_id.sequence_ids:
                    sequence_id = self.journal_id.sequence_ids.filtered(lambda seq: seq.code2.code == self.pay_method_type)
                    if sequence_id:
                        self.next_number = sequence_id.get_next_char(sequence_id.number_next_actual)
                    else:
                        self.next_number = 'Configure un secuencia para el tipo de transaccion que desea realizar'        
                else:
                    self.next_number = 'Configure secuencias para el tipo de transaccion que desea realizar'

    # def recalc(self):  
    #     if self.journal_id.currency_id:
    #         currency_id = self.journal_id.currency_id.with_context(date=self.payment_date)
    #     else:
    #         currency_id = self.journal_id.company_id.currency_id.with_context(date=self.payment_date)
        
    #     for pl in self.payment_line_ids:
    #         line_currency = pl.move_line_id.currency_id or self.journal_id.company_id.currency_id
    #         line_currency_id = pl.currency_id or self.journal_id.company_id.currency_id

    #         amount_original = pl.move_line_id.move_id.amount_total
    #         amount_unreconciled = pl.move_line_id.move_id.amount_residual

    #         pl.amount_original = line_currency._convert(amount_original, currency_id, self.journal_id.company_id, self.payment_date)
    #         pl.amount_unreconcilied = line_currency._convert(amount_unreconciled, currency_id, self.journal_id.company_id, self.payment_date)
    #         if not pl.reconcile:
    #             pl.amount = line_currency_id._convert(pl.amount, currency_id, self.journal_id.company_id, self.payment_date)
    #         else:
    #             pl.amount = pl.amount_unreconcilied
    #         pl.currency_id = currency_id

    # @api.depends('can_edit_wizard', 'amount', 'payment_line_ids')
    # def _compute_payment_difference(self):
    #     for wizard in self:
    #         if wizard.can_edit_wizard and wizard.payment_date:
    #             batch_result = wizard._get_batches()[0]
    #             lines_amount = 0.0
    #             total_amount_residual_in_wizard_currency = wizard\
    #                 ._get_total_amount_in_wizard_currency_to_full_reconcile(batch_result, early_payment_discount=False)[0]

    #             if wizard.payment_line_ids:
    #                 lines_amount = sum(wizard.payment_line_ids.mapped('amount'))
                    
    #             wizard.payment_difference = total_amount_residual_in_wizard_currency - lines_amount
    #         else:
    #             wizard.payment_difference = 0.0

    @api.depends('write_off_lines', 'payment_difference')
    def _compute_writeoff_amount(self):
        for record in self:
            amount = self.payment_difference
            for wo_line in record.write_off_lines:
                amount -= wo_line.debit
                amount += wo_line.credit
            
            record.writeoff_amount = amount

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = {
            'date': self.payment_date,
            'analytic_account_id': self.analytic_account_id.id or False,
            'amount': self.amount,
            'name': self.next_number,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_line_id': self.payment_method_line_id.id,
            'destination_account_id': self.line_ids[0].account_id.id,
            'pay_method_type': self.pay_method_type,
            'write_off_line_vals': []
        }

        if self.payment_difference_handling == 'reconcile':
            if self.early_payment_discount_mode:
                epd_aml_values_list = []
                for aml in batch_result['lines']:
                    if aml.move_id._is_eligible_for_early_payment_discount(self.currency_id, self.payment_date):
                        epd_aml_values_list.append({
                            'aml': aml,
                            'amount_currency': -aml.amount_residual_currency,
                            'balance': aml.currency_id._convert(-aml.amount_residual_currency, aml.company_currency_id, date=self.payment_date),
                        })

                open_amount_currency = self.payment_difference * (-1 if self.payment_type == 'outbound' else 1)
                open_balance = self.currency_id._convert(open_amount_currency, self.company_id.currency_id, self.company_id, self.payment_date)
                early_payment_values = self.env['account.move']._get_invoice_counterpart_amls_for_early_payment_discount(epd_aml_values_list, open_balance)
                for aml_values_list in early_payment_values.values():
                    payment_vals['write_off_line_vals'] += aml_values_list

            elif not self.currency_id.is_zero(self.payment_difference):

                if self.writeoff_is_exchange_account:
                    # Force the rate when computing the 'balance' only when the payment has a foreign currency.
                    # If not, the rate is forced during the reconciliation to put the difference directly on the
                    # exchange difference.
                    if self.currency_id != self.company_currency_id:
                        payment_vals['force_balance'] = sum(batch_result['lines'].mapped('amount_residual'))
                else:
                    if self.payment_type == 'inbound':
                        # Receive money.
                        write_off_amount_currency = self.payment_difference
                    else:  # if self.payment_type == 'outbound':
                        # Send money.
                        write_off_amount_currency = -self.payment_difference

                    if self.write_off_lines:
                        distribution_lines = []
                        for line in self.write_off_lines:
                            if self.payment_type == 'inbound':
                                amount = line.debit
                            else:
                                amount = -line.credit

                            values = {
                                'description': line.description,
                                'account_id': line.account_id.id,
                                'partner_id': line.partner_id.id or self.partner_id.id,
                                'currency_id': self.currency_id.id,
                                'credit': line.credit,
                                'debit': line.debit, 
                                'amount_currency': amount,
                                'analytic_account_id': line.analytic_account_id.id,
                            }
                            distribution_lines.append((0, 0, values))
                        payment_vals['write_off_line'] = distribution_lines
                    else:
                        payment_vals['write_off_line_vals'].append({
                            'name': self.writeoff_label,
                            'account_id': self.writeoff_account_id.id,
                            'partner_id': self.partner_id.id,
                            'currency_id': self.currency_id.id,
                            'amount_currency': write_off_amount_currency,
                            'balance': self.currency_id._convert(write_off_amount_currency, self.company_id.currency_id, self.company_id, self.payment_date),
                        })
        return payment_vals

    # def action_create_payments(self):
    #     payments = super().action_create_payments()

    #     for wizard in self:
    #         if wizard.payment_line_ids:
    #             payment = payments[:1]  # en agrupado debe haber solo 1 pago
    #             for line in wizard.payment_line_ids:
    #                 move_line = line.move_line_id
    #                 if not move_line:
    #                     continue

    #                 # Línea de factura abierta (cuenta por cobrar/pagar)
    #                 inv_lines = move_line.move_id.line_ids.filtered(
    #                     lambda l: l.account_internal_type in ('receivable', 'payable') and not l.reconciled
    #                 )

    #                 # Línea de pago en la misma cuenta
    #                 pay_lines = payment.line_ids.filtered(
    #                     lambda l: l.account_id == inv_lines.account_id and not l.reconciled
    #                 )

    #                 # Reconciliar por el monto definido
    #                 (inv_lines + pay_lines).with_context(
    #                     manual_amount=line.amount
    #                 ).reconcile()

    #     return payments

    # @api.depends('can_edit_wizard', 'source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date', 'payment_line_ids')
    # def _compute_amount(self):
    #     for wizard in self:
    #         if wizard.payment_line_ids:
    #             wizard.amount = sum(wizard.payment_line_ids.mapped("amount"))
    #         else:
    #             super(account_payment_inherit_wizard, wizard)._compute_amount()

class write_off_line(models.TransientModel):
    _name = "account.payment.writeoffline.wizard"
    _description = "Write off lines"

    account_id = fields.Many2one('account.account', string="Cuenta", required=True)
    description = fields.Char(string="Descripcion")
    debit = fields.Float(string="Debito")
    credit = fields.Float(string="Credito")
    amount_currency=fields.Float(string="Monto de Credito")
    currency_id = fields.Many2one('res.currency', string='Moneda')
    payment_id = fields.Many2one('account.payment',string="Pago")
    partner_id	= fields.Many2one('res.partner', string="Empresa")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Cuenta Analitica")
    register_id = fields.Many2one('account.payment.register', string="Registro de pago")

    @api.onchange('account_id')
    def change_account(self):
        if self.account_id:
            if not self.account_id.currency_id:
                self.currency_id = self.env.user.company_id.currency_id.id
            else:
                self.currency_id =  self.account_id.currency_id.id

class account_payment_line_register(models.TransientModel):
    _name = "account.payment.line.register"
    _description = "Lineas de registro de pago"

    move_line_id = fields.Many2one('account.move.line',string="Apuntes")
    account_id = fields.Many2one('account.account',string="Cuenta")
    date_original = fields.Date(string='Fecha')
    date_due = fields.Date(string='Fecha de Vencimiento')
    amount_original = fields.Monetary(currency_field='currency_id',string="Monto Original")
    amount_unreconcilied = fields.Monetary(currency_field='currency_id',string="Monto no conciliado")
    reconcile = fields.Boolean(string="Conciliar totalmente")
    amount = fields.Monetary(currency_field='currency_id',string="Monto")
    payment_id = fields.Many2one('account.payment',string="Payment",ondelete="cascade")
    currency_id = fields.Many2one('res.currency',string='Moneda')
    move_name = fields.Char(string='Move name')
    chqmanalitics=fields.Many2one("account.analytic.account",string="Analitica")
    register_id = fields.Many2one('account.payment.register', string="Registro de pago")

    @api.onchange('move_line_id','amount_original','amount_unreconcilied')
    def _onchange_move(self):
        if self.move_line_id:
            self.account_id = self.move_line_id.account_id.id
            self.amount_original = self.move_line_id.invoice_id.amount_total
            self.date_original = self.move_line_id.date
            self.date_due = self.move_line_id.invoice_id.date_due
            self.amount_unreconcilied = self.move_line_id.invoice_id.residual

    @api.onchange('reconcile')
    def _onchange_reconcile(self):
        if self.reconcile:
            self.amount = self.amount_unreconcilied

    @api.onchange('amount')
    def _onchange_amount(self):
        if self.amount == self.amount_unreconcilied:
            self.reconcile = True
        else:
            self.reconcile = False