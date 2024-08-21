from odoo import api, fields, models
class StockQuant(models.Model):
    _inherit = 'stock.quant'
@api.model
def action_view_quants(self):
    self = self.with_context(search_default_internal_loc=1, search_default_locationgroup=1)
    self = self._set_view_context()
    return self._get_quants_action(extend=True)

