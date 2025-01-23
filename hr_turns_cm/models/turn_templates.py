from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

opt_days = [
    ('0', '1Lun'),('1', '2Mar'),('2', '3Mier'),('3', '4Jue'),
    ('4', '5Vie'),('5', '6Sab'),('6', '7Dom')
]

class turnTemplates(models.Model):
    _name = 'hr.templates.turn'
    _description = 'Plantillas: Plantillas para creacion de turnos'
    _inherit = ['mail.thread','mail.activity.mixin']

    @api.model
    def _get_actual_user(self):
        user_id = self.env.user
        employee_id = self.env['hr.employee'].search([('user_id','=',user_id.id)])
        return employee_id.id

    name = fields.Char('Nombre',tracking=True)
    leader_id = fields.Many2one('hr.employee',string="Lider de Equipo",default=_get_actual_user)
    responsible_id = fields.Many2one('hr.employee',string="Responsable de Equipo",tracking=True)
    active = fields.Boolean(string="Activo", default=True,tracking=True)
    team_id = fields.Many2one('hr.work.teams',string="Equipo")
    template_line_ids = fields.One2many('hr.templates.turn.lines','template_id',string="Lineas de plantilla",copy=True)

    @api.onchange('team_id')
    def change_team(self):
        if self.team_id:
            self.responsible_id = self.team_id.responsible_id.id

    def recalculate_lid(self):
        for line in self.template_line_ids:
            if line.turn_type_a.code == 'LID':
                line.send_values_a_turn()
            if line.turn_type_b.code == 'LID':
                line.send_values_b_turn()

class turnTemplatesLines(models.Model):
    _name = 'hr.templates.turn.lines'
    _description = 'Lineas Plantillas: Lineas para plantillas'

    template_id = fields.Many2one('hr.templates.turn',string="Plantilla")
    day_opt = fields.Selection(opt_days,string="Dia")
    schedule1_in_id = fields.Many2one('hr.options.schedules',string="Entrada 1")
    schedule1_out_id = fields.Many2one('hr.options.schedules',string="Salida 1")
    turn_type_a = fields.Many2one('hr.turn.types',string="Tipo Turno A")
    schedule2_in_id = fields.Many2one('hr.options.schedules',string="Entrada 2")
    schedule2_out_id = fields.Many2one('hr.options.schedules',string="Salida 2")
    turn_type_b = fields.Many2one('hr.turn.types',string="Tipo Turno B")
    editable_a = fields.Boolean(string="Editable A",default=True)
    editable_b = fields.Boolean(string="Editable B",default=True)

    @api.onchange('turn_type_a')
    def send_values_a_turn(self):
        turn_na_id = self.env['hr.options.schedules'].search([('name','=','NA')])
        domain = [('alphabetical','=',False)]
        if self.turn_type_a.opt_turn == '0':
            domain = [('alphabetical','=',True)]
            self.schedule1_in_id = turn_na_id.id
            self.schedule1_out_id = turn_na_id.id
            self.editable_a = False
        else:
            self.schedule1_in_id = False
            self.schedule1_out_id = False
            self.editable_a = True
        return {'domain': {'schedule1_in_id': domain, 'schedule1_out_id': domain}}

    @api.onchange('turn_type_b')
    def send_values_b_turn(self):
        turn_na_id = self.env['hr.options.schedules'].search([('name','=','NA')])
        domain = [('alphabetical','=',False)]
        if self.turn_type_b.opt_turn == '0':
            self.schedule2_in_id = turn_na_id.id
            self.schedule2_out_id = turn_na_id.id
            self.editable_b = False
        else:
            self.schedule2_in_id = False
            self.schedule2_out_id = False
            self.editable_b = True
        return {'domain': {'schedule2_in_id': domain, 'schedule2_out_id': domain}}