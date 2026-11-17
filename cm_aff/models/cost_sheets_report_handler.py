# -*- coding: utf-8 -*-
from odoo import models, api, _

class AffCostSheetsReportHandler(models.AbstractModel):
    _name = 'aff.cost.sheets.report.handler'
    _inherit = 'account.report.custom.handler'
    _description = 'Handler de Datos para Reporte Dinámico de Hojas de Costo'

    # =========================================================================
    # GENERADOR DE LÍNEAS
    # =========================================================================
    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals, warnings=None, **kwargs):
        lines = []

        sheets = self.env['aff.cost.sheets'].search([])
        usd_currency = self.env.ref('base.USD', raise_if_not_found=False) or self.env['res.currency'].search([('name', '=', 'USD')], limit=1)

        def fmt(val):
            if usd_currency:
                return usd_currency.format(val or 0.0)
            return report.format_value(options, val, figure_type='monetary')

        for sheet in sheets:
            sheet_line_id = report._get_generic_line_id('aff.cost.sheets', sheet.id)
            balance_sheet = sheet.estimated_amount - sheet.amount_made

            # NIVEL 0: Hoja de Costo
            lines.append((0, {
                'id': sheet_line_id,
                'name': " ",
                'unfoldable': True,
                'unfolded': True,
                'level': 0,
                'columns': [
                    {'name': 'Monto Estimado'},
                    {'name': 'Monto Realizado'},
                    {'name': 'Diferencia'},
                ],
            }))
            
            # NIVEL 1: Hoja de Costo
            lines.append((0, {
                'id': sheet_line_id,
                'name': f"{sheet.name or 'Hoja de Costos'}",
                'unfoldable': True,
                'unfolded': False,
                'level': 1,
                'columns': [
                    {'name': fmt(sheet.estimated_amount)},
                    {'name': fmt(sheet.amount_made)},
                    {'name': fmt(balance_sheet)},
                ],
            }))

            # NIVEL 2: Aeronaves
            for line in sheet.line_ids:
                aircraft_name = line.aircraft_id.msn if line.aircraft_id else 'Sin Aeronave'
                aircraft_line_id = report._get_generic_line_id('aff.cost.sheets.lines', line.id, parent_line_id=sheet_line_id)
                balance_aircraft = line.estimated_amount - line.amount_made

                lines.append((0, {
                    'id': aircraft_line_id,
                    'name': f"Aeronave: {aircraft_name}",
                    'parent_id': sheet_line_id,
                    'unfoldable': True,
                    'unfolded': False,
                    'level': 2,
                    'columns': [
                        {'name': fmt(line.estimated_amount)},
                        {'name': fmt(line.amount_made)},
                        {'name': fmt(balance_aircraft)},
                    ],
                }))

                # NIVEL 3A: Costos Fijos
                for fixed in line.fixed_cost_ids:
                    fixed_line_id = report._get_generic_line_id('fixed.cost.lines', fixed.id, parent_line_id=aircraft_line_id)
                    cost_name = fixed.cost_id.name if hasattr(fixed, 'cost_id') and fixed.cost_id else 'Costo Fijo'
                    est = getattr(fixed, 'estimated_amount', 0.0)
                    made = getattr(fixed, 'amount_made', 0.0)

                    lines.append((0, {
                        'id': fixed_line_id,
                        'name': f"[Fijo] {cost_name}",
                        'parent_id': aircraft_line_id,
                        'unfoldable': False,
                        'level': 3,
                        'caret_options': 'aff_cost_line',
                        'columns': [
                            {'name': fmt(est)},
                            {'name': fmt(made)},
                            {'name': fmt(est - made)},
                        ],
                    }))

                # NIVEL 3B: Costos Variables
                for variable in line.variable_cost_ids:
                    variable_line_id = report._get_generic_line_id('variable.cost.lines', variable.id, parent_line_id=aircraft_line_id)
                    cost_name = variable.cost_id.name if hasattr(variable, 'cost_id') and variable.cost_id else 'Costo Variable'
                    est = getattr(variable, 'estimated_amount', 0.0)
                    made = getattr(variable, 'amount_made', 0.0)

                    lines.append((0, {
                        'id': variable_line_id,
                        'name': f"[Variable] {cost_name}",
                        'parent_id': aircraft_line_id,
                        'unfoldable': False,
                        'level': 3,
                        'caret_options': 'aff_cost_line',
                        'columns': [
                            {'name': fmt(est)},
                            {'name': fmt(made)},
                            {'name': fmt(est - made)},
                        ],
                    }))

        return lines

    # =========================================================================
    # INICIALIZADOR DE OPCIONES Y ENCABEZADOS (ODOO 19)
    # =========================================================================
    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        
        # Si el motor OWL no ha cargado los títulos, los forzamos explícitamente en options
        if 'columns' in options:
            col_names = [_('Monto Estimado'), _('Monto Realizado'), _('Diferencia')]
            for i, col in enumerate(options['columns']):
                if i < len(col_names):
                    col['name'] = col_names[i]

    # =========================================================================
    # EN ODOO 19: INICIALIZADOR NATIVO DE OPCCIONES DE CARET EN HANDLERS
    # =========================================================================
    def _caret_options_initializer(self):
        """
        Registra el mapeo del caret custom 'aff_cost_line' directamente en este handler
        sin tocar account.move ni afectar otros reportes.
        """
        res = super()._caret_options_initializer() if hasattr(super(), '_caret_options_initializer') else {}
        res['aff_cost_line'] = [
            {
                'name': _('Ver registro'),
                'action': 'action_open_cost_record',
            }
        ]
        return res

    # =========================================================================
    # ACCIÓN AL HACER CLIC EN "VER REGISTRO"
    # =========================================================================
    def action_open_cost_record(self, options, params=None, **kwargs):
        params = params or {}
        raw_line_id = params.get('line_id') or params.get('id') or options.get('line_id') or options.get('id')

        if not raw_line_id:
            return {'type': 'ir.actions.act_window_close'}

        res_model = None
        res_id = None

        try:
            last_segment = str(raw_line_id).split('|')[-1]
            clean_segment = last_segment.strip('~')
            
            if '~' in clean_segment:
                parts = clean_segment.split('~')
                res_model = parts[0]
                res_id = int(parts[1])
            elif '_' in clean_segment:
                parts = clean_segment.rsplit('_', 1)
                res_model = parts[0]
                res_id = int(parts[1])
        except Exception:
            pass

        if not res_model or not res_id:
            return {'type': 'ir.actions.act_window_close'}

        return {
            'type': 'ir.actions.act_window',
            'name': _('Ver registro'),
            'res_model': res_model,
            'res_id': res_id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_warnings(self, report, options):
        """
        Sobreescribe las advertencias globales del framework account.reports 
        únicamente para la instancia de este reporte.
        """
        return {}