from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def process_work_entries_cm(self, date_start, date_stop, force=False):
        date_start = fields.Date.to_date(date_start)
        date_stop = fields.Date.to_date(date_stop)

        if self:
            current_contracts = self._get_contracts(date_start, date_stop, states=['open', 'close'])
        else:
            current_contracts = self._get_all_contracts(date_start, date_stop, states=['open', 'close'])

        return current_contracts.process_work_entry_cm(date_start, date_stop, force=force)
