# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError

class sale_order_inherit(models.Model):
    _inherit = "sale.order"

    airport_tax = fields.Monetary(string="Imp. Aeroportuario", digits=(16, 2), default=0.0)
    currency_rate = fields.Float(string="Tasa de Cambio",digits=(12, 4),compute="get_currency_rate",precompute=True,store=True)
    same_currency = fields.Boolean(string="Misma moneda",compute="get_currency_rate",precompute=True,store=True)
    amount_local_company = fields.Float(string="Moneda Local")

    @api.depends("currency_id",'date_order')
    def get_currency_rate(self):
        for rec in self:
            if rec.currency_id:
                if rec.currency_id != rec.company_id.currency_id:
                    rec.same_currency = False
                    if rec.date_order:
                        rate = rec.currency_id.with_context(date=rec.date_order)
                        rec.currency_rate = 1 / rate.rate
                    else:
                        rate = rec.currency_id.with_context(date=datetime.now().date())
                        rec.currency_rate = 1 / rate.rate
                else:
                    rec.currency_rate = 1
                    rec.same_currency = True

    @api.onchange('amount_total','currency_rate','airport_tax')
    def calculate_amount_local(self):
        self.amount_local_company = self.currency_rate * self.amount_total

    @api.depends('order_line.price_subtotal', 'currency_id', 'company_id', 'payment_term_id','airport_tax')
    def _compute_amounts(self):
        AccountTax = self.env['account.tax']
        for order in self:
            order_lines = order._get_priced_lines()
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            base_lines += order._add_base_lines_for_early_payment_discount()
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
            )
            # tax_totals['total_amount_currency'] += order.airport_tax
            order.amount_untaxed = tax_totals['base_amount_currency']
            order.amount_tax = tax_totals['tax_amount_currency']
            order.amount_total = (tax_totals['total_amount_currency'] + order.airport_tax)


    @api.depends_context('lang')
    @api.depends(
        'order_line.price_subtotal',
        'currency_id',
        'company_id',
        'payment_term_id',
        'airport_tax'
    )
    def _compute_tax_totals(self):
        AccountTax = self.env['account.tax']

        for order in self:
            order_lines = order._get_priced_lines()

            base_lines = [
                line._prepare_base_line_for_taxes_computation()
                for line in order_lines
            ]

            base_lines += order._add_base_lines_for_early_payment_discount()

            AccountTax._add_tax_details_in_base_lines(
                base_lines,
                order.company_id
            )

            AccountTax._round_base_lines_tax_details(
                base_lines,
                order.company_id
            )

            tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
            )

            # Impuesto aeroportuario
            airport_tax = order.airport_tax or 0.0
            tax_totals['airport_tax'] = airport_tax

            # Agregarlo al total de la cotización
            tax_totals['total_amount_currency'] += airport_tax

            # Si la moneda de la cotización es la misma que
            # la moneda de la compañía
            if order.currency_id == order.company_id.currency_id:
                tax_totals['total_amount'] += airport_tax
            else:
                tax_totals['total_amount'] += order.currency_id._convert(
                    airport_tax,
                    order.company_id.currency_id,
                    order.company_id,
                    order.date_order.date(),
                )

            order.tax_totals = tax_totals

class order_line_inherit(models.Model):
    _inherit = "sale.order.line"

    departure_date = fields.Date(string="Ida")
    return_date = fields.Date(string="Regreso")
    yq_amount = fields.Monetary(string="YQ", digits=(16, 2), default=0.0)

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_ids', 'yq_amount')
    def _compute_amount(self):
        return super()._compute_amount()

    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        self.ensure_one()

        base_line = super()._prepare_base_line_for_taxes_computation(**kwargs)

        if self.yq_amount:
            quantity = base_line.get('quantity', 1.0) or 1.0

            # Agregamos el YQ al precio unitario de la base fiscal
            base_line['price_unit'] += self.yq_amount

        return base_line

# class AccountTaxInh(models.Model):
#     _inherit = 'account.tax'

#     @api.model
#     def _prepare_base_line_for_taxes_computation(self, record, **kwargs):
#         res = super(AccountTaxInh, self)._prepare_base_line_for_taxes_computation(record, **kwargs)
#         if isinstance(record, self.env['sale.order.line'].__class__):
#             res['yq_amount'] = (record.yq_amount)
#         return res