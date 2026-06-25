import base64
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class settlementExpensesCont(http.Controller):

    @http.route('/expenses/settlement_expenses', type='http', auth="user", website=True)
    def custom_option(self, **kwargs):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
        expenses_categories = request.env['product.product'].sudo().search([('company_id','=',employee_id.company_id.id),('can_be_expensed','=',True)])
        expense_request_id = request.env['cm.expenses.request'].sudo().search([('assign_to_id','=',employee_id.id),('state','in',['assigned'])])
        pending_expense = 'not_allow'
        message_form = ''
        amount_assign = 0
        if len(expense_request_id) == 1:
            pending_expense = 'allow'
            amount_assign = expense_request_id.advance_amount
        if len(expense_request_id) == 0:
            message_form = "No tiene viaticos asignados para liquidar"

        expenses_data = []
        expenses_ids = request.env['hr.expense'].sudo().search([('request_id','=',expense_request_id.id)])
        deposit_id = False
        if expense_request_id:
            deposit_id = request.env['banks.deposit'].sudo().search([('request_id','=',expense_request_id.id),('state','=','validated')])

        if expenses_ids:
            for expense in expenses_ids:
                att_created = False
                if expense.nb_attachment != 0:
                    att_created = True

                expenses_data.append({
                    'description': expense.description,
                    'name': expense.name,
                    'invoice_number': expense.invoice_number,
                    'date': expense.date.strftime('%d/%m/%Y'),
                    'amount': expense.total_amount_currency,
                    'category': expense.product_id.name,
                    'att_created': att_created,
                    'id': expense.id
                })

        if deposit_id:
            expenses_data.append({
                'description': "Deposito creado",
                'name': deposit_id.name,
                'invoice_number': deposit_id.number,
                'date': deposit_id.date.strftime('%d/%m/%Y'),
                'amount': deposit_id.total,
                'att_created': False,
                'category': 'Deposito'
            })

        values = {
            "expenses_categories": expenses_categories,
            'show_form': pending_expense,
            'request_id': expense_request_id.id,
            'number_request': expense_request_id.name,
            'assign_to': expense_request_id.assign_to_id.name,
            'purpose': expense_request_id.purpose,
            'amount_assign': amount_assign,
            'balance_employee_amount': round(expense_request_id.balance_employee_amount, 2),
            'expenses_data': expenses_data,
            'message_form': message_form
        }
        return request.render("cm_expenses_request.portal_settlement_expense", values)

    @http.route('/create_expense/submit', type='http', auth="user", methods=["POST"], website=True)
    def hours_form_submit(self, **post):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)

        action = post.get('action')
        if action == 'save':
            date = post.get("date_record")
            expense_type_id = post.get("selection_expense_category")
            invoice_number = post.get("invoice_record")
            description = post.get("description_record")
            amount = post.get("amount")
            notes = post.get("record_notes") or False
            request_id = post.get("request_id")
            
            # Obtener los archivos adjuntos
            uploaded_files = request.httprequest.files.getlist('rec_expenses_attachments')

            rec_request_id = request.env['cm.expenses.request'].sudo().browse(int(request_id))
            product_id = request.env['product.product'].sudo().browse(int(expense_type_id))

            budget_account_id = False
            if product_id:
                budget_account_id = request.env['account.budget.account'].search([('process_id','=',rec_request_id.process_id.id),('category_expense_id','=',product_id.id)])
                if budget_account_id:
                    budget_account_id = budget_account_id.id
                else:
                    raise ValidationError(f"""La categoria de gasto {self.product_id.name} no tiene configurada una cuenta de presupuesto, consulte con el encargado de gastos.""")

            values = {
                'name': description,
                'invoice_number': invoice_number,
                'product_id': int(expense_type_id),
                'description': notes or description,
                'employee_id': rec_request_id.assign_to_id.id,
                'process_id': rec_request_id.process_id.id,
                'reason_expense': rec_request_id.reason_expense,
                'total_amount_currency': amount,
                'budget_account_id': budget_account_id,
                'request_id': int(request_id)
            }

            if rec_request_id.assign_to_id.analytic_account_id:
                analytic = rec_request_id.assign_to_id.analytic_account_id.id
                values['analytic_distribution'] = {str(analytic): 100.0}

            expense_id = request.env['hr.expense'].sudo().create(values)

            # --- Lógica de adjuntos ---
            for uploaded_file in uploaded_files:
                if uploaded_file and uploaded_file.filename:
                    attachment_data = base64.b64encode(uploaded_file.read())
                    # Crea el adjunto
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': uploaded_file.filename,
                        'datas': attachment_data,
                        'res_model': 'hr.expense',    # Modelo al que se adjunta
                        'res_id': expense_id.id,      # ID del registro de la solicitud de ausencia
                        'type': 'binary',
                        'mimetype': uploaded_file.content_type,
                    })
                    # attachment_ids_to_link.append(attachment.id)

        return request.redirect('/expenses/settlement_expenses')

    @http.route('/create_expense_deposit',type='http',auth='user',methods=['POST'],website=True)
    def create_expense_line(self, **post):
        user = request.env.user
        employee_id = request.env['hr.employee'].sudo().search(
            [('user_id', '=', user.id)],
            limit=1
        )
        date = post.get("date_record")
        amount = post.get("amount_balance")
        request_id = post.get("request_id")

        account_id = request.env['account.account'].sudo().search([('code','=','105.01')])
        journal_id = request.env['account.journal'].sudo().search([('code','=','BACL')])
        rec_request_id = request.env['cm.expenses.request'].sudo().browse(int(request_id))
        
        deposit_id = self.env['banks.deposit'].sudo().create({
            'journal_id': journal_id.id,
            'date': date,
            'doc_type': 'deposit',
            'total': amount,
            'name': f"""Reembolso {employee_id.name}""",
            'request_id': rec_request_id.id
        })

        request.env['banks.deposit.name'].sudo().create({
            'account_id': account_id.id,
            'name': "Reembolso",
            'amount': amount,
            'chqmanalitics': rec_request_id.assign_to_id.analytic_account_id.id or False,
            'mcheck_id': deposit_id.id,
            'type': 'cr'
        })
        deposit_id.sudo().action_validate()
        rec_request_id.sudo().write({'refund_amount': amount})

        return request.redirect('/expenses/settlement_expenses')

    @http.route('/finalize_expense_request', type='http', auth='user', methods=['POST'], website=True)
    def finalize_expense_request(self, **post):
        request_id = int(post.get('request_id'))

        expense_request_id = request.env['cm.expenses.request'].sudo().browse(request_id)
        expense_request_id.sudo().with_context({'state':'pending'}).change_state()

        request.session['flash_message'] = (
            'La liquidación fue finalizada correctamente.'
        )
        request.session['flash_message_type'] = 'alert-success'

        return request.redirect(
            '/expenses/settlement_expenses'
    )

    @http.route('/delete_expense_line',type='http',auth='user',methods=['POST'],website=True)
    def delete_expense_line(self, **post):
        expense_line_id = int(post.get('expense_line_id'))
        expense_line = request.env['hr.expense'].sudo().browse(expense_line_id)
        try:
            admin = request.env.ref('base.user_admin')
            expense_line.with_user(admin).unlink()
        except Exception as e:
            print("ERROR:", repr(e))
            raise

        request.session['flash_message'] = (
            'Gasto eliminado correctamente.'
        )
        request.session['flash_message_type'] = 'alert-success'

        return request.redirect(
            '/expenses/settlement_expenses'
        )