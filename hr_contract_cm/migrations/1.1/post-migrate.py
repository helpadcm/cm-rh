import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    this function will migrate the data from odoo studio fields to the new fields.
    expect to remove old fields from the model manually.

    The function does the following:
    - Fetches all the contract records
    - Checks if any of the old fields exist in the model
    - If none of the old fields exist, the function does nothing
    - If any of the old fields exist, the function copies the data from the old fields to the new fields
    - The max_transportation_bonus field is calculated as x_studio_max_transportation_bonus / 100
    - The value_bonus field is set to 100 for all records
    """
    _logger.info('Migrating data from old fields to new fields')
    contracts = api.Environment(cr, SUPERUSER_ID, {}).get('hr.contract').search([])
    old_fields = ['x_studio_early_checkin_bonus_time', 'x_studio_late_checkout_bonus_time', 'x_studio_max_extra_hours',
                  'x_studio_max_performance_bonus', 'x_studio_max_transportation_bonus']
    model_fields = api.Environment(cr, SUPERUSER_ID, {}).get('hr.contract').fields_get().keys()
    if not any(field in model_fields for field in old_fields):
        _logger.info('Old fields not found in model')
        return

    _logger.info(f'Old fields found in model, where found {len(contracts)} records to migrate')
    for contract in contracts:
        contract.early_checkin_bonus_time = contract.x_studio_early_checkin_bonus_time
        contract.late_checkout_bonus_time = contract.x_studio_late_checkout_bonus_time
        contract.max_extra_hours = contract.x_studio_max_extra_hours
        contract.value_bonus = 100
