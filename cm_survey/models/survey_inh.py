# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError,ValidationError

class survey_inherit(models.Model):
    _inherit = "survey.survey"

    result_ids = fields.One2many('survey.results','survey_id',string="Resultados")
    show_ranking = fields.Boolean(string="Ver Ranking")

    def get_results(self):
        if self.result_ids:
            self.result_ids.unlink()

        survey_input_ids = self.env['survey.user_input'].search([('survey_id','=',self.id)])
        partner_ids = []
        results = []
        if survey_input_ids:
            for result in survey_input_ids:
                if result.partner_id:
                    total_points = sum(result.user_input_line_ids.mapped('answer_score'))
                    vals = {
                        'survey_id': self.id,
                        'partner_id': result.partner_id.id,
                        'points': total_points,
                        'percentage': result.scoring_percentage
                    }
                    if result.partner_id.id in partner_ids:
                        if vals.get('points') < total_points:
                            results[partner_ids.index(result.partner_id.id)]['points'] = total_points
                    else:
                        partner_ids.append(result.partner_id.id)
                        results.append(vals)

        if results:
            ordered = sorted(results, key=lambda x: x['points'], reverse=True)
            for o in ordered[:5]:
                self.env['survey.results'].create(o)

class survey_results(models.Model):
    _name = "survey.results"
    _description = "Resultados de encuesta"

    survey_id = fields.Many2one('survey.survey',string="Encuesta")
    partner_id = fields.Many2one('res.partner',string="Participante")
    points = fields.Integer(string="Puntos")
    percentage = fields.Float(string="Porcentaje(%)")