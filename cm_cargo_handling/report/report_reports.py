# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ReportCargoManifest(models.AbstractModel):
    _name = 'report.cm_cargo_handling.report_cargo_manifest'
    _description = "manifiesto"
    
    @api.model
    def render_html(self, docids, data=None):
        obj_manifests=self.env['cargo.manifest'].browse(docids)
        docargs = {
            'docs': obj_manifests
        }
        return self.env['report'].render('cm_cargo_manifest.report_cargo_manifest', docargs)

    @api.model
    def render_xls(self, docids, data=None):
        docargs = {
            'docs': docids
        }
        return docargs