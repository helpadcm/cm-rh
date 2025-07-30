from odoo import models, fields, api, _

class account_payment_inherit(models.TransientModel):
    _inherit= "account.payment.register"

    def _get_batches(self):
        res = super(account_payment_inherit, self)._get_batches()
        if self.env.context.get('params'):
            params = self.env.context.get('params')
            model = params.get('model')
            if model == 'sale.order.handling':
                active_id = params.get('id')
                order_id = self.env['sale.order.handling'].browse(active_id)
                if order_id:
                    payment_values = res[0].get('payment_values')
                    if order_id.parent_id:
                        payment_values.update({'partner_id': order_id.parent_id.id})
        return res