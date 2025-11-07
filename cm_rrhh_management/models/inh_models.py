from odoo import models, fields, api

class departmentRRHHInh(models.Model):
    _inherit = 'hr.department'

    apply_ranking = fields.Boolean(string="Aplica a Ranking Puntualidad")
    request_approve_id = fields.Many2one('hr.employee',string="Aprobador de prestamos")

class employeeRRHHInh(models.Model):
    _inherit = 'hr.employee'

    template_id = fields.Many2one('hr.templates.turn',string="Plantilla de Horario")
    role_in_loans = fields.Selection([('evaluator_rrhh','Evaluador'),('evaluator_finance','Aprobador Finanzas'),('check_creator','Emisor de Cheque')],string="Role en prestamos")

class employeePublicRRHHInh(models.Model):
    _inherit = 'hr.employee.public'

    template_id = fields.Many2one('hr.templates.turn',string="Plantilla de Horario")
    role_in_loans = fields.Selection([('evaluator_rrhh','Evaluador'),('evaluator_finance','Aprobador Finanzas'),('check_creator','Emisor de Cheque')],string="Role en prestamos")