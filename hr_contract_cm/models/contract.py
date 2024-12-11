from odoo import fields, models , api


class Contract(models.Model):
    _inherit = 'hr.contract'

    early_checkin_bonus_time = fields.Float(
        string='Hora de Bono de Entrada',
        help='Hora de Bono de Trasporte de Entrada Temprana',
        tracking=True
    )
    late_checkout_bonus_time = fields.Float(
        string='Hora de Bono de Salida Tarde',
        help='Hora de Bono de Trasporte de Salida Tarde',
        tracking=True
    )
    max_extra_hours = fields.Float(
        string='Máximo de Horas Extras',
        help='Máximo de horas extras que el empleado puede realizar',
        tracking=True
    )
    max_performance_bonus = fields.Monetary(
        string='Máximo de Bono de Desempeño',
        help='Bono de Desempeño que se le otorgara al empleado',
        tracking=True
    )

    max_transportation_bonus = fields.Integer(
        string='Bono de Trasporte Máximo',
        help='Bono de Trasporte Máximo',
        tracking=True
    )
    value_bonus = fields.Monetary(
        string='Valor de Bono',
        help='Valor unitario del bono de transporte',
        tracking=True
    )

    @api.model
    def cron_update_contract_bonus(self):
        value_bonus = 100
        contracts = self.env['hr.contract'].search([])
        for contract in contracts:
            contract.write({"value_bonus": value_bonus,
                            "early_checkin_bonus_time": contract.x_studio_early_checkin_bonus_time,
                            "late_checkout_bonus_time": contract.x_lat_checkout_bonus_time,
                            "max_extra_hours": contract.x_studio_max_extra_hours,
                            "max_performance_bonus": contract.x_studio_max_performance_bonus,
                            "max_transportation_bonus": contract.x_studio_max_transportation_bonus / value_bonus
                            })

    def show_historical_salary(self):
        payslip_line_ids =  self.env['hr.payslip.line'].search([('employee_id','=',self.employee_id.id)])
        print ("/////////////////////////")
        net_line_ids = []
        for line in payslip_line_ids:
            if line.salary_rule_id.code == 'NET':
                net_line_ids.append(line.id)
        print (net_line_ids)  
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lista de salarios netos',
            'view_mode': 'tree',
            'res_model': 'hr.payslip.line',
            'views': [(self.env.ref('hr_contract_cm.view_payslip_cm_line_tree').id, 'tree')],
            'domain': [('id','=',net_line_ids)],
            'target': 'current',
            'context': self.env.context
        }
