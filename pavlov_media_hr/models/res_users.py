# Copyright (C) 2019 Pavlov Media
# License Proprietary. Do not copy, share nor distribute.

from odoo import api, models, fields


class Users(models.Model):
    _inherit = 'res.users'

    hr_job_id = fields.Many2one('hr.job', 'Job Position')
    hr_job_title = fields.Char("Job Title")
    hr_department_id = fields.Many2one('hr.department', string="Department")
    hr_parent_id = fields.Many2one('hr.employee', string="Manager")
    user_template_id = fields.Many2one('res.users', string="User Template")
    child_user_ids = fields.One2many('res.users',
                                     'user_template_id',
                                     string="Users")

    @api.onchange('hr_job_title',
                  'hr_job_id',
                  'hr_department_id',
                  'hr_parent_id')
    def on_change_update_employee_fields(self):
        if self.employee_ids:
            for record in self.employee_ids:
                record.write({
                    'job_title': self.hr_job_title,
                    'job_id': self.hr_job_id.id,
                    'department_id': self.hr_department_id.id,
                    'parent_id': self.hr_parent_id.id})

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id
