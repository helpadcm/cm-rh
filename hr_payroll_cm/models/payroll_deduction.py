from odoo import api, fields, models, _

from dateutil.relativedelta import relativedelta


class HrSalaryAttachmentDeduction(models.Model):
    _inherit = 'hr.salary.attachment'

    first_date_payment = fields.Date(
        'Fecha de inicio del pago', default=False, tracking=True,
        help='Fecha de comienzo de pagos', )

    @api.depends('state', 'total_amount', 'monthly_amount', 'date_start')
    def _compute_estimated_end(self):
        for record in self:
            if record.state not in ['close', 'cancel'] and record.total_amount and record.monthly_amount:
                rate = self.compute_rate()
                record.compute_first_date_payment()
                record.compute_date_estimated_end(rate)
            else:
                record.date_estimated_end = None
                record.first_date_payment = None

    def compute_rate(self):
        rate = self.total_amount / self.monthly_amount

        return rate

    def compute_first_date_payment(self):
        self.first_date_payment = self.date_start.replace(
            month=self.date_start.month
            if self.date_start.day <= 15
            else self.date_start.month + 1,
            day=15 if 1 < self.date_start.day <= 15 else 1
        )

    def compute_date_estimated_end(self, rate):
        num_moths = (rate - 1) // 2
        num_days = 15 if ((rate - 1) % 2) > 0 else 0
        num_moths = int(num_moths)
        num_days = int(num_days)

        if self.first_date_payment.day == 15 and num_days == 15:
            num_moths += 1
            num_days = 1

        self.date_estimated_end = self.first_date_payment + relativedelta(
            months=num_moths, day=num_days or self.first_date_payment.day
        )