import logging
from datetime import timedelta

from odoo import models

_logger = logging.getLogger(__name__)


class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    def update_work_entry_type_by_planning(self):
        for work_entry in self:
            if work_entry.state != 'draft':
                continue
            if not work_entry.planning_slot_id:
                continue
            if not work_entry.planning_slot_id.role_id.work_entry_type_id:
                # Supone que todos los roles que no tienen work_entry_type_id
                # no cuentan como horas trabajadas
                work_entry.unlink()
                self -= work_entry
                continue
            work_entry_type = work_entry.planning_slot_id.role_id.work_entry_type_id
            work_entry.write({'work_entry_type_id': work_entry_type.id})

    def _update_overtime_type(self, max_ordinary):
        """
        This method updates the type of overtime for each work entry in the recordset.

        It iterates over each work entry in the recordset. If the duration of the work entry
        is greater than the maximum ordinary hours, it updates the end time of the work entry
        and creates a new work entry with the remaining hours. The new work entry has the same
        properties as the original one, but with updated start and stop times and duration.

        If the duration of the work entry is less than or equal to the maximum ordinary hours,
        it subtracts the duration of the work entry from the maximum ordinary hours.

        :param max_ordinary: The maximum number of ordinary hours.
        :type max_ordinary: float
        :return: Entries with updated work entry types.
        """
        entries = self.env['hr.work.entry']
        ordinary_worked_hours = 0
        for entry in self:
            _logger.info(f'Entry: {entry}, Duration: {entry.duration}, Max Ordinary: {max_ordinary}')
            entries += entry
            if max_ordinary <= 0:
                entry.write({'work_entry_type_id': self.env.ref('planning_cm.cm_work_entry_type_125').id})
            elif entry.duration > max_ordinary:
                # Update end_time and create a new work entry with the remaining hours
                remaining_hours = entry.duration - max_ordinary
                entry.date_stop = entry.date_start + timedelta(hours=max_ordinary)
                entry.duration = max_ordinary
                # Create a new work entry with the remaining hours
                new_entry = entry.copy(
                    {
                        'date_start': entry.date_stop,
                        'date_stop': entry.date_stop + timedelta(hours=remaining_hours),
                        'duration': remaining_hours,
                        'work_entry_type_id': self.env.ref('planning_cm.cm_work_entry_type_125').id,
                        }
                    )
                entries += new_entry
                max_ordinary = 0
                ordinary_worked_hours += entry.duration
            else:
                max_ordinary -= entry.duration
                ordinary_worked_hours += entry.duration

        return entries, ordinary_worked_hours
