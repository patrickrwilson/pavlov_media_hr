# Copyright (C) 2019 Pavlov Media
# Copyright (C) 2019 Open Source Integrators
# License Proprietary. Do not copy, share nor distribute.
{
    'name': 'Pavlov Media - Human Resources',
    'summary': 'Pavlov Media Configuration and Data for HR',
    'version': '12.0.1.1.0',
    'license': 'Other proprietary',
    'author': 'Pavlov Media',
    'maintainer': 'Pavlov Media, Open Source Integrators',
    'website': 'https://www.pavlovmedia.com',
    'depends': [
        'helpdesk',
        'hr_appraisal',
        'hr_attendance',
        'hr_expense',
        'hr_expense_operating_unit',
        'hr_holidays',
        'hr_timesheet',
        'timesheet_grid',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_timesheet.xml',
        'views/hr_employee.xml',
        'views/hr_expense.xml',
        'views/res_users_views.xml',
    ],
    'development_status': 'Beta',
    'maintainers': ['patrickrwilson'],
}
