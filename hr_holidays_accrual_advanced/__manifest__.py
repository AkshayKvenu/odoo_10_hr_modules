# Copyright 2018-2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Advanced Accrual Allocation',
    'version': '10.0.1.0.3',
    'category': 'Human Resources',
    'website': 'https://github.com/OCA/hr',
    'author':
        'Brainbean Apps, '
        'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'summary': 'Advanced accrual leaves allocation',
    'depends': [
        'hr',
        'hr_holidays',
        'hr_employee_service',
    ],
    'data': [
        'security/hr_holidays_accrual_security.xml',
        'security/ir.model.access.csv',
        'wizards/hr_leave_allocation_accrual_calculator.xml',
        'views/hr_leave_allocation.xml',
        'views/hr_leave_allocation_accruement.xml',
        'views/hr_leave.xml',
    ],
}
