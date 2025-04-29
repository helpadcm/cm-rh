from math import ceil

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

class HrSalaryAttachment(models.Model):
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
            if record.date_start.day > 16:
                record.first_date_payment = record.date_start + relativedelta(months=1, day=1)
            elif record.date_start.day == 1:
                record.first_date_payment = record.date_start
            else:
                record.first_date_payment = record.date_start + relativedelta(day=16)

    def _compute_date_estimated_end(self, number_of_payments):
        for record in self:
            first_date = record.first_date_payment
            current_date = first_date

            for _ in range(number_of_payments - 1):  # Iteramos hasta el último pago
                if current_date.day <= 15:  
                    # Si está en la primera quincena (1-15), ir al día 16>
                    current_date = current_date + relativedelta(day=16)
                else:  
                    # Si está en la segunda quincena (16-fin de mes), ir al día 1 del próximo mes
                    current_date = current_date + relativedelta(months=1, day=1)
            
            record.date_estimated_end = current_date

