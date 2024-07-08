from odoo import http
from odoo.http import request


class DownloadController(http.Controller):
    @http.route('/download/attendance_reports', type='http', auth="user")
    def download_attendance_reports(self, **kwargs):
        # Assuming `export_to_excel_for_multiple_employees` is a method of a model
        # You need to adjust `model_name` and possibly retrieve additional parameters from `kwargs`
        Model = request.env['your.model.name'].sudo()
        zip_content, file_name = Model.export_to_excel_for_multiple_employees()

        return request.make_response(
            zip_content,
            [
                ('Content-Type', 'application/zip'),
                ('Content-Disposition', 'attachment; filename="%s"' % file_name),
                ]
            )
