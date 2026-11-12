# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_talento_humano = fields.Boolean(string='Para Talento Humano', default=False)


class HrEmployeeIndumentariaLine(models.Model):
    _name = 'hr.employee.indumentaria.line'
    _description = 'Línea de Indumentaria de Empleado'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, ondelete='cascade')
    
    tipo_activo = fields.Selection([
        ('uniforme', 'Uniforme'),
        ('epp', 'EPP')
    ], string='Tipo de Activo', required=True, default='uniforme')

    product_id = fields.Many2one(
        'product.product', 
        string='Artículo', 
        required=True,
        domain="[('is_talento_humano', '=', True)]"
    )
    
    color = fields.Char(string='Color')
    observaciones = fields.Char(string='Observaciones')
    
    # Campo para obtener la talla dinámicamente de las variantes del producto
    talla = fields.Char(string='Talla', compute='_compute_talla', store=True)

    @api.depends('product_id', 'product_id.product_template_attribute_value_ids')
    def _compute_talla(self):
        for line in self:
            talla_val = ''
            if line.product_id:
                for attr_val in line.product_id.product_template_attribute_value_ids:
                    if 'talla' in attr_val.attribute_id.name.lower():
                        talla_val = attr_val.name
                        break
                if not talla_val and line.product_id.product_template_attribute_value_ids:
                    talla_val = ', '.join(line.product_id.product_template_attribute_value_ids.mapped('name'))
            line.talla = talla_val

    quantity = fields.Float(string='Cantidad', default=1.0, required=True)
    
    fecha_entrega = fields.Date(
        string='Fecha de Entrega', 
        default=fields.Date.context_today, 
        required=True
    )
    
    fecha_reposicion = fields.Date(
        string='Fecha de Reposición'
    )

    state = fields.Selection([
        ('draft', 'Pendiente de Entrega'),
        ('delivered', 'Entregado')
    ], string='Estado', default='draft', tracking=True)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    indumentaria_line_ids = fields.One2many(
        'hr.employee.indumentaria.line', 
        'employee_id', 
        string='Indumentaria Asignada'
    )

    def action_deliver_indumentaria(self):
        """Acción del botón: procesa la entrega y asegura la descarga del PDF si hay uniformes"""
        self.ensure_one()
        lines = self.indumentaria_line_ids
        if not lines:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Aviso',
                    'message': 'No hay artículos de indumentaria registrados para este empleado.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
            
        # Actualiza a 'delivered' las líneas que estén pendientes
        for line in lines.filtered(lambda l: l.state == 'draft'):
            line.state = 'delivered'
            line.fecha_entrega = fields.Date.context_today(self)

        # Verifica si hay al menos un artículo de tipo 'uniforme'
        has_uniforme = any(line.tipo_activo == 'uniforme' for line in lines)

        if has_uniforme:
            # Retorna la acción para descargar el PDF de forma directa
            return self.env.ref('hr_employee_cm.action_report_indumentaria_cm').report_action(self)
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Éxito',
                    'message': 'Indumentaria (EPP) entregada correctamente.',
                    'type': 'success',
                    'sticky': False,
                }
            }