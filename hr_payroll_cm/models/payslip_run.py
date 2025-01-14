from odoo import models, api

months = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.onchange('date_start')
    def get_payslip_name(self):
        if self.date_start:
            if self.date_start.day == 1:
                self.name = '1ra Quincena mes %s del año %s'%(months[self.date_start.month - 1], self.date_start.year)
            if self.date_start.day == 16:
                self.name = '2da Quincena mes %s del año %s'%(months[self.date_start.month - 1], self.date_start.year)

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

    def action_hr_payroll_payslips_report(self):
        """
        Load the payroll report in the system.
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payroll.payslips.report',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'payslip_run_id': self.id,
                },
            }
