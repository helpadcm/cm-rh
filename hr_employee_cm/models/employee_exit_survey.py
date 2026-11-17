from odoo import models, fields, api

class EmployeeExitSurvey(models.Model):
    _name = 'employee.exit.survey'
    _description = 'Entrevista de Salida de Empleado'
    _rec_name = 'employee_name'

    # Datos del Colaborador
    employee_id = fields.Many2one('hr.employee', string="Empleado")
    employee_name = fields.Char(string="Nombre del Colaborador")
    job_title = fields.Char(string="Puesto")
    department_name = fields.Char(string="Departamento")
    manager_name = fields.Char(string="Jefe Inmediato")
    first_contract_date = fields.Date(string="Fecha de Ingreso")
    departure_date = fields.Date(string="Fecha de Salida")
    seniority = fields.Char(string="Antigüedad")
    
    # Tipo de Salida
    departure_type = fields.Selection([
        ('Renuncia voluntaria', 'Renuncia voluntaria'),
        ('Terminación de contrato', 'Terminación de contrato'),
        ('Decisión de la empresa', 'Decisión de la empresa'),
        ('Otro', 'Otro')
    ], string="Tipo de Salida")
    other_departure_text = fields.Char(string="Especificar Tipo de Salida")

    # Campo visual para mostrar "Otro (DETALLE)" en la lista
    departure_type_display = fields.Char(string="Tipo de Salida", compute='_compute_departure_type_display', store=True)

    @api.depends('departure_type', 'other_departure_text')
    def _compute_departure_type_display(self):
        for record in self:
            if record.departure_type == 'Otro' and record.other_departure_text:
                record.departure_type_display = f"Otro ({record.other_departure_text})"
            else:
                record.departure_type_display = record.departure_type or ''

    # Motivo de Salida
    main_reason = fields.Selection([
        ('Mejor oportunidad laboral', 'Mejor oportunidad laboral'),
        ('Mejor salario o beneficios', 'Mejor salario o beneficios'),
        ('Falta de oportunidades de crecimiento profesional', 'Falta de oportunidades de crecimiento profesional'),
        ('Relación con el jefe inmediato', 'Relación con el jefe inmediato'),
        ('Ambiente laboral', 'Ambiente laboral'),
        ('Horarios o turnos de trabajo', 'Horarios o turnos de trabajo'),
        ('Motivos personales o familiares', 'Motivos personales o familiares'),
        ('Estudios o desarrollo profesional', 'Estudios o desarrollo profesional'),
        ('Condiciones de trabajo', 'Condiciones de trabajo'),
        ('Insatisfacción con las funciones del puesto', 'Insatisfacción con las funciones del puesto'),
        ('Reubicación o cambio de residencia', 'Reubicación o cambio de residencia'),
        ('Otro', 'Otro')
    ], string="Motivo Principal")
    
    other_reason_text = fields.Char(string="Especificar Motivo")
    other_factors = fields.Text(string="Otros Factores")

    # Campo visual para mostrar "Otro (DETALLE)" en reportes/listas
    main_reason_display = fields.Char(string="Motivo Principal", compute='_compute_main_reason_display', store=True)

    @api.depends('main_reason', 'other_reason_text')
    def _compute_main_reason_display(self):
        for record in self:
            if record.main_reason == 'Otro' and record.other_reason_text:
                record.main_reason_display = f"Otro ({record.other_reason_text})"
            else:
                record.main_reason_display = record.main_reason or ''

    # Escala de Calificación
    EXPERIENCE_SCALE = [
        ('1', 'Muy insatisfecho'),
        ('2', 'Insatisfecho'),
        ('3', 'Neutral'),
        ('4', 'Satisfecho'),
        ('5', 'Muy satisfecho'),
        ('NA', 'No aplica')
    ]

    q1 = fields.Selection(EXPERIENCE_SCALE, string="1. Herramientas y equipos")
    q2 = fields.Selection(EXPERIENCE_SCALE, string="2. Condiciones de instalaciones")
    q3 = fields.Selection(EXPERIENCE_SCALE, string="3. Ambiente laboral")
    q4 = fields.Selection(EXPERIENCE_SCALE, string="4. Comunicación y equipo")
    q5 = fields.Selection(EXPERIENCE_SCALE, string="5. Liderazgo y jefe")
    q6 = fields.Selection(EXPERIENCE_SCALE, string="6. Claridad de funciones")
    q7 = fields.Selection(EXPERIENCE_SCALE, string="7. Carga laboral")
    q8 = fields.Selection(EXPERIENCE_SCALE, string="8. Oportunidades de capacitación")
    q9 = fields.Selection(EXPERIENCE_SCALE, string="9. Salario")
    q10 = fields.Selection(EXPERIENCE_SCALE, string="10. Beneficios laborales")
    q11 = fields.Selection(EXPERIENCE_SCALE, string="11. Reconocimiento")
    q12 = fields.Selection(EXPERIENCE_SCALE, string="12. Expectativas al ingresar")

    # Preguntas Abiertas
    positive_aspects = fields.Text(string="Aspectos Positivos")
    improvement_aspects = fields.Text(string="Aspectos a Mejorar")
    manager_relationship = fields.Text(string="Relación con el Jefe")
    growth_opportunities = fields.Text(string="Oportunidades de Crecimiento")
    retention_actions = fields.Text(string="Acciones de Retención")
    what_would_change = fields.Text(string="Qué Cambiaría")
    would_recommend = fields.Selection([
        ('yes', 'Sí'),
        ('no', 'No'),
        ('maybe', 'Tal vez')
    ], string="¿Recomendaría la Empresa?")
    would_recommend_why = fields.Text(string="¿Por qué?")
    additional_comments = fields.Text(string="Comentarios Adicionales")

    # ==========================================
    # CONVERSIÓN AUTOMÁTICA A MAYÚSCULAS
    # ==========================================
    @api.model_create_multi
    def create(self, vals_list):
        text_fields = {
            'employee_name', 'job_title', 'department_name', 'manager_name',
            'seniority', 'other_departure_text', 'other_reason_text', 'other_factors',
            'positive_aspects', 'improvement_aspects', 'manager_relationship',
            'growth_opportunities', 'retention_actions', 'what_would_change',
            'would_recommend_why', 'additional_comments'
        }
        for vals in vals_list:
            for key, val in list(vals.items()):
                if key in text_fields and isinstance(val, str):
                    vals[key] = val.upper()
        return super().create(vals_list)

    def write(self, vals):
        text_fields = {
            'employee_name', 'job_title', 'department_name', 'manager_name',
            'seniority', 'other_departure_text', 'other_reason_text', 'other_factors',
            'positive_aspects', 'improvement_aspects', 'manager_relationship',
            'growth_opportunities', 'retention_actions', 'what_would_change',
            'would_recommend_why', 'additional_comments'
        }
        for key, val in list(vals.items()):
            if key in text_fields and isinstance(val, str):
                vals[key] = val.upper()
        return super().write(vals)
        