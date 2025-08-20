from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    retention_line_ids = fields.One2many(
        'account.payment.register.retention.line',
        'wizard_id',
        string="Retentions"
    )
    total_retention = fields.Monetary(
        string="Total Retention", compute="_compute_total_retention", store=True
    )
    original_amount = fields.Monetary(string="Original Amount", readonly=True)
    apply_retentions = fields.Boolean(string="Aplicar Retenciones")

    @api.depends('retention_line_ids.amount', 'amount')
    def _compute_total_retention(self):
        for wizard in self:
            original_amount = sum(
                wizard.line_ids.mapped('amount_currency' if wizard.currency_id else 'balance')
            )
            total = sum(wizard.retention_line_ids.mapped('amount'))
            wizard.total_retention = round(total, 2)
            wizard.original_amount = original_amount
            # if total > original_amount:
            #     raise ValidationError(
            #         "El total de las retenciones no puede ser mayor que el monto original del pago."
            #     )

    @api.depends('can_edit_wizard', 'amount', 'total_retention')
    def _compute_payment_difference(self):
        res = super(AccountPaymentRegister, self)._compute_payment_difference()
        for rec in self:
            rec.payment_difference -= rec.total_retention
        return res

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)

        # Adjuntamos las retenciones en los valores del payment
        if self.apply_retentions:
            vals.update({'apply_retentions': self.apply_retentions})
            retentions = []
            for line in self.retention_line_ids:
                if line.account_id and line.amount:
                    retentions.append((0, 0, {
                        'account_id': line.account_id.id,
                        'amount': line.amount,
                        'name': f'Retención: {line.account_id.name}',
                        'percentage': line.percentage,
                        'amount_currency': line.amount_currency,
                        'company_currency_id': line.company_currency_id.id,
                        'currency_id': line.currency_id.id,
                        'base_amount': line.base_amount,
                        'invoice_id': line.invoice_line_id.move_id.id
                    }))
            vals['retention_line_ids'] = retentions
        return vals

class AccountPaymentRegisterRetentionLine(models.TransientModel):
    _name = 'account.payment.register.retention.line'
    _description = 'Líneas de retención en el registro de pago'

    wizard_id = fields.Many2one('account.payment.register', required=True, ondelete='cascade')
    invoice_line_id = fields.Many2one(
        'account.move.line',
        string="Factura",
        domain="[('move_id', 'in', parent.line_ids.move_id.ids), ('account_id.internal_type', '=', 'payable')]"
    )
    account_id = fields.Many2one('account.account', string='Cuenta de retención', required=True)
    percentage = fields.Float(string='Porcentaje (%)', required=True)
    # apply_percentage_payment = fields.Float(string="Porcentaje del pago")
    name = fields.Char(string="Descripcion")
    amount = fields.Monetary(string='Monto', compute='_compute_amount')
    currency_id = fields.Many2one(related='wizard_id.currency_id', readonly=True)
    amount_currency = fields.Float(string='Amount Currency')
    company_currency_id = fields.Many2one(related='wizard_id.company_id.currency_id', string="Moneda de la empresa", readonly=True)
    base_amount = fields.Float(string='Base Amount',compute='_compute_amount')

    @api.depends('invoice_line_id', 'percentage')
    def _compute_amount(self):
        for line in self:
            wizard = line.wizard_id

            amount_untaxed = abs(line.invoice_line_id.move_id.amount_untaxed)
            line.amount = float(round((line.account_id.retention_porcent/100) * amount_untaxed, 2))
            line.base_amount = amount_untaxed

    @api.onchange('account_id', 'invoice_line_id')
    def get_data_account(self):
        self.env.context = dict(self.env.context or {})
        self.name = self.account_id.tax_description
        self.percentage = self.account_id.retention_porcent


    @api.onchange('amount','currency_id')
    def onchange_amount(self):
        if self.currency_id != self.company_currency_id:
            self.amount_currency = self.company_currency_id._convert(
                self.amount,
                self.currency_id,
                self.wizard_id.company_id,
                self.wizard_id.payment_date
            )
        else:
            self.amount_currency = self.amount
