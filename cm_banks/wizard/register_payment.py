# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class account_payment_inherit_wizard(models.TransientModel):
    _inherit= "account.payment.register"

    next_number = fields.Char(string='Siguiente Numero', help='El numero siguiente del cheque o transferencia', default="Borrador")
    writeoff_amount = fields.Float(string="Diferencia", compute='_compute_writeoff_amount')
    write_off_lines = fields.One2many('account.payment.writeoffline', 'register_id', string="Write off lines")
    invoice_compute = fields.Many2many('account.move.line', string="move lines")
    # payment_line_ids = fields.One2many('account.payment.line', 'register_id',string="Lineas de pago")
    pay_method_type= fields.Selection([
                ('check','Check'),
                ('transference','Transference'),
                ('otros','Otros')], string='Tipo de transaccion')

    @api.model
    def default_get(self, fields):
        rec = super(account_payment_inherit_wizard, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        invoices = self.env[active_model].browse(active_ids)
        #domain=[('move_id','in',invoices.ids),('full_reconcile_id','=',False),('partner_id','=',rec.get('partner_id'))]
        if invoices[0].move_type == 'in_invoice':
            type_account = 'liability_payable'
        if invoices[0].move_type == 'out_invoice':
            type_account = 'asset_receivable'
        move_line_obj = invoices.filtered(lambda line: line.reconciled == False and line.account_id.account_type == type_account)
        pay_line_ids = []
        for ml in move_line_obj:
            vals = {
                'move_line_id': ml.id,
                'account_id': ml.account_id.id,
                'amount_original': ml.move_id.amount_total,
                'date_original': ml.date,
                'date_due': ml.date_maturity,
                'amount_unreconcilied': ml.move_id.amount_residual,
                'amount': ml.amount_residual,
                'reconcile': True
            }
            pay_line_ids.append((0, 0, vals))
        rec.update({
            'invoice_compute': [(6, 0, active_ids)],
            # 'payment_line_ids': pay_line_ids
        })
        return rec

    @api.onchange('journal_id', 'pay_method_type')
    def onchange_journal(self):
        if self.journal_id:
            if self.partner_type == 'customer':
                if self.journal_id.sequence_id:
                    sequence_id = self.journal_id.sequence_id
                    next_number = sequence_id.get_next_char(sequence_id.number_next_actual)
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
            'amount': self.amount,
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
                        for line in self.write_off_lines:
                            if self.payment_type == 'inbound':
                                amount = line.debit
                            else:
                                amount = -line.credit

                            values = {
                                'name': line.description,
                                'account_id': line.account_id.id,
                                'partner_id': line.partner_id.id or self.partner_id.id,
                                'currency_id': self.currency_id.id,
                                'amount_currency': amount,
                                'balance': self.currency_id._convert(amount, self.company_id.currency_id, self.company_id, self.payment_date),    
                            }
                            payment_vals['write_off_line_vals'].append(values)
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

class write_off_line(models.TransientModel):
    _name = "account.payment.writeoffline"
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
