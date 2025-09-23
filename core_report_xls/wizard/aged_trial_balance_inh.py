# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountAgedTrialBalanceInh(models.TransientModel):
    _inherit = 'account.aged.trial.balance'

    @api.model
    def _get_currency_default(self):
        base_USD = self.env.ref('base.USD')
        return base_USD.id

    currency_id = fields.Many2one('res.currency', string="Moneda", default=_get_currency_default)

    def _get_report_data(self, data):
        res = super(AccountAgedTrialBalanceInh, self)._get_report_data(data)
        res['form'].update(self.read(['currency_id'])[0])
        return res