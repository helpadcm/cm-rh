from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HrSalaryAttachmentDeduction(models.Model):
    _inherit = 'hr.salary.attachment'

    first_date_payment = fields.Date(
        'Fecha de inicio del pago',
        default=False,
        compute='_compute_first_date_payment',
        help='Fecha de comienzo de pagos', )

    @api.depends('state', 'total_amount', 'monthly_amount', 'date_start', 'first_date_payment')
    def _compute_estimated_end(self):
        for record in self:
            if record.state not in ['close', 'cancel'] and record.total_amount and record.monthly_amount:
                rate = record._compute_rate(record.total_amount, record.monthly_amount)
                record._compute_date_estimated_end(rate)
            else:
                record.date_estimated_end = None
                record.first_date_payment = None

    @staticmethod
    def _compute_rate(total_amount, monthly_amount):
        rate = total_amount / monthly_amount

        return rate

    @api.depends('date_start')
    def _compute_first_date_payment(self):
        for record in self:
            # TODO(helpad): Pasar a usar relativedelta en lugar de replace
            record.first_date_payment = record.date_start.replace(
                month=record.date_start.month
                if record.date_start.day <= 15
                else record.date_start.month + 1,
                day=15 if 1 < record.date_start.day <= 15 else 1
                )

    def _compute_date_estimated_end(self, rate):
        for record in self:
            num_moths = (rate - 1) // 2
            num_days = 15 if ((rate - 1) % 2) > 0 else 0
            num_moths = int(num_moths)
            num_days = int(num_days)

            if record.first_date_payment.day == 15 and num_days == 15:
                num_moths += 1
                num_days = 1

            record.date_estimated_end = record.first_date_payment + relativedelta(
                months=num_moths, day=num_days or record.first_date_payment.day
                )
