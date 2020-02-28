# Copyright (C) 2019 Pavlov Media
# Copyright (C) 2019 Open Source Integrators
# License Proprietary. Do not copy, share nor distribute.

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    expense_corporate_id = fields.Many2one(
        'res.users', string="Expense Corporate",
        domain=lambda self:
        [('groups_id', 'in',
          self.env.ref('hr_expense.group_hr_expense_user').id)],
        help="User responsible of expense approval."
             "Should be an Expense Manager.")

    @api.onchange('job_title',
                  'job_id',
                  'department_id',
                  'parent_id')
    def on_update_user_fields(self):
        for record in self:
            if record.user_id:
                record.user_id.write({
                    'hr_job_title': record.job_title,
                    'hr_job_id': record.job_id.id,
                    'hr_department_id': record.department_id.id,
                    'hr_parent_id': record.parent_id.id})
