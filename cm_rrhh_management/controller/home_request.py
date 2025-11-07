from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class requestHomePortal(http.Controller):

    @http.route('/requests_cm/request_home_cm', type='http', auth="user", website=True)
    def custom_option(self, **kwargs):
        values = {
        }
        return request.render("cm_rrhh_management.portal_request_home_cm", values)