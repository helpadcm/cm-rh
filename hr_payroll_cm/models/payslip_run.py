from odoo import models


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_load_nomina_from_excel_wizard(self):
        """
        Open the wizard to load the payroll from an excel file.
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'load.nomina.from.excel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payslip_run_id': self.id
                }
            }

    def action_load_catorceavo_from_excel_wizard(self):
        """
        Open the wizard to load the catorceavo from an excel file.
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'load.catorceavo.from.excel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payslip_run_id': self.id
                }
            }
