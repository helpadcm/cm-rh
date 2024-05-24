from math import ceil

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HrSalaryAttachmentDeduction(models.Model):
    _inherit = 'hr.salary.attachment'

    first_date_payment = fields.Date(
        'Fecha de inicio de pago',
        compute='_compute_first_date_payment',
        help='Fecha de comienzo de pagos', )

    @api.depends('state', 'total_amount', 'monthly_amount', 'date_start', 'first_date_payment')
    def _compute_estimated_end(self):
        for record in self:
            if record.state not in ['close', 'cancel'] and record.total_amount and record.monthly_amount:
                payments = record._compute_number_of_payments(record.total_amount, record.monthly_amount)
                record._compute_date_estimated_end(payments)
            else:
                record.date_estimated_end = False

    @staticmethod
    def _compute_number_of_payments(total_amount, monthly_amount):
        if monthly_amount == 0:
            return 0
        number_of_payments = ceil(total_amount / monthly_amount)
        return number_of_payments

    @api.depends('date_start')
    def _compute_first_date_payment(self):
        for record in self:
            if record.date_start.day > 15:
                record.first_date_payment = record.date_start + relativedelta(months=1, day=1)
            elif record.date_start.day == 1:
                record.first_date_payment = record.date_start
            else:
                record.first_date_payment = record.date_start + relativedelta(day=15)

    def _compute_date_estimated_end(self, number_of_payments):
        for record in self:
            num_moths = int((number_of_payments - 1) // 2)
            num_days = int(((number_of_payments - 1) % 2) * 15)

            if record.first_date_payment.day == 15 and num_days == 15:
                num_moths += 1
                num_days = 1

            record.date_estimated_end = record.first_date_payment + relativedelta(
                months=num_moths, day=num_days or record.first_date_payment.day
                )
