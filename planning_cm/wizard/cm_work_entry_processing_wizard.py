from odoo import models, _
from odoo.exceptions import ValidationError


class CmWorkEntryProcessingWizard(models.TransientModel):
    _inherit = 'hr.work.entry.regeneration.wizard'

    def process_work_entries_cm(self):
        self.ensure_one()

        if not self.valid:
            raise ValidationError(
                _(
                    "In order to regenerate the work entries, you need to provide the wizard with an employee_id, "
                    "a date_from and a date_to. In addition to that, the time interval defined by date_from and "
                    "date_to must not contain any validated work entries."
                    )
                )

        if self.date_from < self.earliest_available_date or self.date_to > self.latest_available_date:
            raise ValidationError(
                _(
                    "The from date must be >= '%(earliest_available_date)s' and the to date must be <= '%("
                    "latest_available_date)s', which correspond to the generated work entries time interval.",
                    earliest_available_date=self._date_to_string(self.earliest_available_date),
                    latest_available_date=self._date_to_string(self.latest_available_date)
                    )
                )

        date_from = max(
            self.date_from, self.earliest_available_date
            ) if self.earliest_available_date else self.date_from
        date_to = min(self.date_to, self.latest_available_date) if self.latest_available_date else self.date_to

        self.employee_ids.process_work_entries_cm(date_from, date_to, True)

        return {'type': 'ir.actions.act_window_close'}
