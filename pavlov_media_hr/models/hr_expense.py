# Copyright (C) 2019 Pavlov Media
# Copyright (C) 2019 Open Source Integrators
# License Proprietary. Do not copy, share nor distribute.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class HrExpense(models.Model):
    _inherit = "hr.expense"

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('approved', 'Manager Approved'),
        ('corporate', 'Corporate Approved'),
        ('done', 'Paid'),
        ('refused', 'Refused')
    ], compute='_compute_state', string='Status', copy=False, index=True,
        readonly=True, store=True, help="Status of the expense.")

    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_state(self):
        res = super()._compute_state()
        for expense in self:
            if expense.sheet_id.state == "corporate" or \
                    expense.sheet_id.state == "post":
                expense.state = "corporate"
        return res

    @api.multi
    def approve_expense_sheets(self):
        res = super().approve_expense_sheets()
        # Check State
        if self.state == 'reported':
            if self.employee_id.expense_manager_id != self.env.user and \
                    self.employee_id.expense_corporate_id != self.env.user:
                raise UserError(_("You are not the Manager/Corporate Approver"
                                  " for this employee"))
            elif self.employee_id.expense_corporate_id == self.env.user:
                responsible_id = self.user_id.id or self.env.user.id
                self.write({'state': 'corporate', 'user_id': responsible_id})
                self.activity_update()
            else:
                responsible_id = self.user_id.id or self.env.user.id
                self.write({'state': 'approved', 'user_id': responsible_id})
        elif self.state == 'approved':
            if self.employee_id.expense_corporate_id != self.env.user:
                raise UserError(_("You are not the Corporate Approver for "
                                  "this employee"))
            else:
                responsible_id = self.user_id.id or self.env.user.id
                self.write({'state': 'corporate', 'user_id': responsible_id})
                self.activity_update()
        return res

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state in ['done', 'corporate']:
                raise UserError(_('You cannot delete a posted or approved '
                                  'expense.'))
        return super(HrExpense, self).unlink()


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    expense_line_ids = fields.One2many(
        'hr.expense', 'sheet_id', string='Expense Lines',
        states={'approve': [('readonly', True)],
                'corporate': [('readonly', True)],
                'done': [('readonly', True)],
                'post': [('readonly', True)]},
        copy=False)

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('submit', 'Submitted'),
        ('approve', 'Manager Approved'),
        ('corporate', 'Corporate Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('cancel', 'Refused')
    ], string='Status', copy=False, index=True, readonly=True, store=True,
        help="Status of the expense.")

    @api.multi
    def approve_expense_sheets(self):
        # Check State
        if self.state == 'submit':
            if self.employee_id.expense_manager_id != self.env.user and \
                    self.employee_id.expense_corporate_id != self.env.user:
                raise UserError(_("You are not the Manager/Corporate Approver "
                                  "for this employee"))
            elif self.employee_id.expense_corporate_id == self.env.user:
                responsible_id = self.user_id.id or self.env.user.id
                self.write({'state': 'corporate', 'user_id': responsible_id})
                self.activity_update()
                return True
            else:
                responsible_id = self.user_id.id or self.env.user.id
                self.write({'state': 'approve', 'user_id': responsible_id})
        elif self.state == 'approve':
            if self.employee_id.expense_corporate_id != self.env.user:
                raise UserError(_("You are not the Corporate Approver for "
                                  "this employee"))
            else:
                responsible_id = self.user_id.id or self.env.user.id
                self.write({'state': 'corporate', 'user_id': responsible_id})
                self.activity_update()
                return True
        return super().approve_expense_sheets()

    @api.multi
    def action_sheet_move_create(self):
        if any(sheet.state != 'corporate' for sheet in self):
            raise UserError(_("You can only generate accounting entry for "
                              "approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal "
                              "specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids').filtered(
            lambda r: not float_is_zero(
                r.total_amount,
                precision_rounding=(
                        r.currency_id or
                        self.env.user.company_id.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        self.activity_update()
        return res

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'corporate':
            return 'hr_expense.mt_expense_approved'
        elif 'state' in init_values and self.state == 'cancel':
            return 'hr_expense.mt_expense_refused'
        elif 'state' in init_values and self.state == 'done':
            return 'hr_expense.mt_expense_paid'
        return super(HrExpenseSheet, self)._track_subtype(init_values)

    def activity_update(self):
        for expense_report in self.filtered(lambda hol: hol.state == 'submit'):
            self.activity_schedule(
                'hr_expense.mail_act_expense_approval',
                user_id=expense_report.sudo()._get_responsible_for_approval().
                id)
        self.filtered(lambda hol: hol.state == 'corporate').\
            activity_feedback(['hr_expense.mail_act_expense_approval'])
        self.filtered(lambda hol: hol.state == 'cancel').\
            activity_unlink(['hr_expense.mail_act_expense_approval'])
