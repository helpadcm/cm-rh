# -*- coding: utf-8 -*-
import base64
from odoo import api, models,fields, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError,ValidationError

class groupGuides(models.Model):    
    _name = 'cargo.invoice.group_guides'
    _description = "Facturacion grupo de guias"
    _inherit = ['mail.thread','mail.activity.mixin']

    @api.model
    def _get_default_date(self):
        return datetime.now().date()

    name = fields.Char(string="Numero", tracking=True, default="Borrador")
    state = fields.Selection([('draft','Borrador'),('validated','Validado')],string="Estado",default="draft", tracking=True)
    partner_id = fields.Many2one('res.partner',string="Cliente", tracking=True)
    date = fields.Date(string="Fecha",default=_get_default_date, tracking=True)
    number_guide = fields.Char(string="Numero de guias")
    guide_ids = fields.One2many('cargo.invoice.group_guides.lines','group_invoice_id',string="Lista de guias")
    move_id = fields.Many2one('account.move',string="Factura")
    total = fields.Float(string="Total", compute='_get_amount_total', store=True)

    @api.depends('guide_ids')
    def _get_amount_total(self):
        for rec in self:
            if rec.guide_ids:
                rec.total = sum(rec.guide_ids.mapped('amount'))
            else:
                rec.total = 0

    def set_to_draft(self):
        if self.move_id.state == 'draft':
            attachments = self.env['ir.attachment'].search([('res_model', '=', 'account.move'),('res_id', '=', self.move_id.id)])
            attachments.unlink()

            self.move_id.unlink()
        elif self.move_id.payment_state in ['paid','partial','in_payment']:
            raise ValidationError("No se puede regresar a borrador cuando la factura ya tiene registrado un pago.")    
        self.state = 'draft'

    @api.onchange('number_guide')
    def onchange_bill_landing_barcode(self):
        if self.number_guide:
            if not self.partner_id:
                raise ValidationError("Antes de agregar guias debe seleccionar un cliente")

            bill_landings_list = []
            actual_ids = []
            for cbl in self.guide_ids:
                actual_ids.append(cbl.bill_id.id)

            barcode = self.number_guide
            bill_landings = self.env['cargo.bill'].search([('name','=',barcode),('id', 'not in', actual_ids),('group_invoice_id','=',False),('order_id.partner_id','=',self.partner_id.id)])
            for bl in bill_landings:
                vals = {'bill_id': bl.id}
                bill_landings_list.append((0, 0, vals))
            self.guide_ids = bill_landings_list
            self.number_guide = False

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            bill_landings_list = []
            if self.guide_ids:
                self.guide_ids.unlink()

            bill_landings = self.env['cargo.bill'].search([('group_invoice_id','=',False),('order_id.partner_id','=',self.partner_id.id),('order_id.state','not in',['quote','canceled'])])
            for bl in bill_landings:
                if not bl.order_id.move_id:
                    vals = {'bill_id': bl.id}
                    bill_landings_list.append((0, 0, vals))
            self.guide_ids = bill_landings_list

    def create_invoice(self):
        journal_id = self.env['account.journal'].search([('code','=','INV')])
        usd_currency_id = self.env.ref('base.USD')

        move_vals = {
            'partner_id': self.partner_id.id,
            'partner_name': self.partner_id.name,
            'rtn_name': self.partner_id.vat,
            'move_type': 'out_invoice',
            'group_invoice_id': self.id,
            'invoice_user_id': self.env.user.id,
            'modality': 'credit',
            'from_handling': True,
            'journal_id': journal_id.id,
            'invoice_date': self.date,
            'currency_id': usd_currency_id.id,
            'state': 'draft',
            'name': 'Borrador',
            'internal_number': 'Borrador',
        }

        self.move_id = self.env['account.move'].create(move_vals)
        
        report = self.env.ref('cm_cargo_handling.action_guide_format')
        attachment_obj = self.env['ir.attachment']
        attach_vals = {
            'type': 'binary',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'mimetype': 'application/pdf',
        }
        for guide in self.guide_ids:

            line_vals = {
                'product_id': guide.bill_id.product_id.id,
                'partner_id': self.partner_id.id,
                'name': guide.bill_id.product_id.name,
                'account_id': guide.bill_id.product_id.property_account_income_id.id,
                'price_unit': guide.bill_id.order_id.total,
                'move_id': self.move_id.id,
                'tax_ids': [(6, 0, guide.bill_id.product_id.taxes_id.ids)]
            }
            self.env.cr.execute("""
                SELECT account_budget_account_id
                FROM account_account_account_budget_account_rel
                WHERE account_account_id = %s
            """, (guide.bill_id.product_id.property_account_income_id.id,))
            rows = self.env.cr.fetchall()

            if len(rows) > 0:
                try:
                    budget_account_id = rows[0][0]
                except:
                    budget_account_id = False

            if budget_account_id:
                source_id = self.env['crossovered.source_expenditure'].search([('code','=','VT')])
                process_id = self.env['crossovered.activity'].search([('code','=','PP06-COM')])
                line_vals.update({
                    'analytic_account_id': budget_account_id,
                    'activity_id': process_id.id,
                    'source_id': source_id.id
                })

            self.env['account.move.line'].create(line_vals)
            if not guide.bill_id.order_id.move_id:
                guide.bill_id.order_id.move_id = self.move_id.id


            data = {
                'order_id': guide.bill_id.order_id.id,
                'print_guides': True,
            }

            pdf_content, _ = self.env['ir.actions.report'].with_context(active_ids=[self.move_id.id])._render_qweb_pdf(
                report.report_name,
                [self.move_id.id],
                data=data
            )
            
            attach_vals.update({'datas': base64.b64encode(pdf_content), 'name': f'Guias {guide.bill_id.name}.pdf'})
            attachment_obj.create(attach_vals)

        sequence_id = self.env.ref('cm_cargo_handling.sequence_guide_group_handling')
        if self.name == 'Borrador':
            self.write({'name': sequence_id.next_by_id()})    
        self.write({'state': 'validated'})

    def show_invoice(self):
        return {
            'name': _('Factura'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.move_id.id,
            'target': 'current',
            'context': {},
        }

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError("Solo se pueden borrar registros en estado borrador")
        res = super(groupGuides, self).unlink()
        return res

class groupGuidesList(models.Model):    
    _name = 'cargo.invoice.group_guides.lines'
    _description = "Listado de guias"

    group_invoice_id = fields.Many2one('cargo.invoice.group_guides',string="Grupo")
    bill_id = fields.Many2one('cargo.bill',string="Guia")
    amount = fields.Float(string="Monto(USD)",related="bill_id.order_id.total")
    amount_lps = fields.Float(string="Monto(LPS)",related="bill_id.order_id.amount_total_lps")
    currency_id = fields.Many2one('res.currency',string="Moneda",related="bill_id.order_id.external_currency_id")
    currency_hnl_id = fields.Many2one('res.currency',string="Moneda HNL",related="bill_id.order_id.local_currency_id")
    date = fields.Datetime(string="Fecha", related="bill_id.create_date")
