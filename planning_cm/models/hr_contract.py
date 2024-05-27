import logging
from datetime import datetime, timedelta

from odoo import models, fields

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    def process_work_entry_cm(self, date_start, date_stop, force=False):
        assert not isinstance(date_start, datetime)
        assert not isinstance(date_stop, datetime)

        date_start = datetime.combine(fields.Datetime.to_datetime(date_start), datetime.min.time())
        date_stop = datetime.combine(fields.Datetime.to_datetime(date_stop), datetime.max.time())

        work_entries = self._process_work_entry_cm(date_start, date_stop, force=force)
        return work_entries

    def _process_work_entry_cm(self, date_start, date_stop, force=False):
        # This method filter to get all contracts that use planning,
        # then process the work entries with the function update_work_entry_type
        # based on the planning rules.
        # Later, fillter all the normal work entries and call the function process_overtime_cm
        work_entry_model = self.env['hr.work.entry']
        planning_based_contracts = self.filtered(lambda c: c.work_entry_source == 'planning')
        if not planning_based_contracts:
            return work_entry_model
        work_entries = work_entry_model.search(
            [
                ('contract_id', 'in', planning_based_contracts.ids),
                ('date_start', '<=', date_stop),
                ('date_stop', '>=', date_start),
                ]
            )
        if not work_entries:
            return work_entry_model
        work_entries.update_work_entry_type_by_planning()
        work_entries = work_entry_model.search(
            [
                ('contract_id', 'in', planning_based_contracts.ids),
                ('date_start', '<=', date_stop),
                ('date_stop', '>=', date_start),
                ]
            )
        for contract in planning_based_contracts:
            work_entries = contract._process_overtime_cm(work_entries, date_start, date_stop)
        return work_entries

    @staticmethod
    def _process_overtime_cm(work_entries, date_start, date_stop):
        # This method filter to get all contracts that use planning,
        # For every week in the interval process the week work entries with 
        # the funcion _update_overtime_type based on the cm rules.
        
        # TODO: Adicionar como m anejar tipos de asistencia especiales.

        # Calculate the week intervals
        number_of_weeks = (date_stop - date_start).days // 7
        no_week_days = (date_stop - date_start).days % 7

        ordinary_hours_per_week = 44
        result = work_entries.env['hr.work.entry']

        for week in range(number_of_weeks):
            _logger.info(f'Week: {week}')
            week_ordinary_worked_hours = 0
            week_start = date_start + timedelta(days=7 * week)
            week_end = week_start + timedelta(days=7)
            week_work_entries = work_entries.filtered(
                lambda wwe, ws=week_start, we=week_end: ws <= wwe.date_start < we
                )
            for day in range(7):
                day_start = week_start + timedelta(days=day)
                day_end = day_start + timedelta(days=1)
                day_work_entries = week_work_entries.filtered(
                    lambda dwe, ds=day_start, de=day_end: ds <= dwe.date_start < de
                    )
                if not day_work_entries:
                    continue
                # If week_worked_hours is greater than ordinary_hours_per_week
                # call the method change_overtime_type
                max_day_ordinary_hours = min(max(ordinary_hours_per_week - week_ordinary_worked_hours, 0), 8)
                day_work_entries, ordinary_worked_hours = day_work_entries._update_overtime_type(max_day_ordinary_hours)
                week_ordinary_worked_hours += ordinary_worked_hours
                result += day_work_entries
                _logger.info(
                    f'Week: {week + 1}, Day: {day}, Day Work Entries: {day_work_entries} with duration: '
                    f'{sum(day_work_entries.mapped("duration"))}'
                    )
                _logger.info(
                    f'ordinary_hours_per_week: {ordinary_hours_per_week}, week_worked_hours: '
                    f'{week_ordinary_worked_hours}'
                    )
                _logger.info(f'overtime: {max(sum(day_work_entries.mapped("duration")) - max_day_ordinary_hours, 0)}')

        if no_week_days > 0:
            for day in range(no_week_days):
                day_start = date_stop - timedelta(days=no_week_days) + timedelta(days=day)
                day_end = day_start + timedelta(days=1)
                day_work_entries = work_entries.filtered(
                    lambda dwe, ds=day_start, de=day_end: ds <= dwe.date_start < de
                    )
                if not day_work_entries:
                    continue
                result += day_work_entries._update_overtime_type(8)
                _logger.info(
                    f'Week: {number_of_weeks + 1}, Day: {day}, Day Work Entries: {day_work_entries} with duration: '
                    f'{sum(day_work_entries.mapped("duration"))}'
                    )

        return result
