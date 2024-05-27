from odoo import api, fields, models


class HrWorkEnty(models.Model):
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
                continue
            work_entry_type = work_entry.planning_slot_id.role_id.work_entry_type_id
            work_entry.write({'work_entry_type_id': work_entry_type.id})
