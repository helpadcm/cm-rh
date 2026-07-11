from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    retention_line_ids = fields.One2many('account.payment.retention.line', 'payment_id', string="Retentions")
    total_retention = fields.Monetary(string="Total Retention", compute="_compute_total_retention", store=True)
    real_payment_amount = fields.Monetary(string="Amount After Retention", compute="_compute_total_retention", store=True)
    apply_retentions = fields.Boolean(string="Aplicar Retenciones")
    retentions_applied = fields.Boolean(string='Retenciones Aplicadas')
    retention_lines_detail = fields.One2many('retentions','pay_number',string="Detalles de Retencion")

    @api.depends('retention_line_ids.amount', 'amount')
    def _compute_total_retention(self):
        for payment in self:
            total = sum(payment.retention_line_ids.mapped('amount'))
            payment.total_retention = total
            payment.real_payment_amount = payment.amount - total

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        line_vals = super()._prepare_move_line_default_vals(write_off_line_vals)
        total_retention = 0
        total_amount_currency = 0
        for payment in self:
            if payment.apply_retentions:
                retention_lines = []
                for retention in payment.retention_line_ids:
                    payment.create_retention_detail(payment, retention)

                    if payment.payment_type == 'outbound':
                        if payment.currency_id.name != payment.company_id.currency_id.name:
                            amount_currency = -retention.amount_currency
                        else:
                            amount_currency = -retention.amount_currency
                    else:
                        amount_currency = retention.amount_currency

                    total_retention += retention.amount
                    total_amount_currency += abs(amount_currency)

                    if not retention.account_id or not retention.amount:
                        continue

                    vals = {
                        'name': f'Retención: {retention.account_id.name}',
                        'date_maturity': payment.date,
                        'amount_currency': amount_currency,
                        'currency_id': payment.currency_id.id,
                        'partner_id': payment.partner_id.id,
                        'account_id': retention.account_id.id,
                    }

                    if payment.payment_type == 'outbound':
                        vals.update({'balance': retention.amount * -1})
                    else:
                        vals.update({'balance': retention.amount})

                    retention_lines.append(vals)

                # Ajustar línea bancaria (donde está el crédito del pago)
                for line in line_vals:
                    if payment.payment_type == 'outbound':
                        line['balance'] += total_retention
                        line['amount_currency'] += (total_amount_currency)
                        break
                    elif payment.payment_type == 'inbound':
                        line['balance'] += total_retention
                        line['amount_currency'] += (total_amount_currency * -1)
                        break

                # Agregar las líneas de retención
                line_vals.extend(retention_lines)
        return line_vals

    def create_retention_detail(self, payment, retention):
        vals = {}
        num = ""
        cai_shot = ""
        cai_range = ""
        min_number_shot = ""
        max_number_shot = ""
        cai_expires_shot = False
        cai_id = False
        sequence_ids = self.env.get('ir.sequence').with_context(no_update=False).search([('code','=','retentions.number')])
        for sequence_id in sequence_ids:
            num = sequence_id.next_by_id()
            if len(sequence_id.cai_ids) > 0:
                if self.date  > sequence_id.expiration_date:
                    raise ValidationError(_('la fecha de expiracion para este CAI es %s ') %(sequence_id.expiration_date))
                if sequence_id.number_next_actual - 1 > sequence_id.max_value :
                    raise ValidationError(_('Se ha consumido el rango autorizado %s - %s ') %(sequence_id.min_value, sequence_id.max_value))
            for regimen in sequence_id.cai_ids:
                if regimen.selected:
                    cai_shot = regimen.cai_id.name
                    cai_id = regimen.cai_id.id
                    cai_expires_shot = regimen.cai_id.expiration_date
                    min_number_shot = sequence_id.dis_min_value
                    max_number_shot = sequence_id.dis_max_value
        vals.update({
            'pay_number': payment.id,
            'name': num,
            'description': retention.name,
            'invoice_id': retention.invoice_id.id,
            'partner_name': payment.partner_id.name,
            'partner_rtn': payment.partner_id.vat,
            'date': self.date,
            'doc_issue_date': retention.invoice_id.invoice_date,
            'state': 'close',
            'cai': retention.invoice_id.cai_id.id,
            'cai_shot': retention.invoice_id.cai_id.name,
            'cai_ret': cai_shot,
            'cai_ret_id': cai_id,
            # 'cai_range': cai_range,
            'cai_expires_shot': cai_expires_shot,
            'min_number_shot': min_number_shot,
            'max_number_shot': max_number_shot,
            #'car_range':car_range,
            'doc_type': 'voucher',
            'ref_doc_type': 'invoice',
        })
        retention_id = self.env['retentions'].create(vals)
        retention.retention_id = retention_id.id
        payment.write({'retentions_applied':True})
        return retention_id

    def action_cancel(self):
        res = super(AccountPayment, self).action_cancel()
        for payment in self:
            if payment.apply_retentions:
                for ret in self.retention_lines_detail:
                    ret.write({'state': 'cancel'})
        return res