# -*- coding: utf-8 -*-
{
    'name': "Payroll Overtime",

    'summary': """
        Payroll Overtime""",

    'description': """
        Payroll Overtime
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.3',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_payroll','hr_attendance'],

    # always loaded
    'data': [
        'data/ir_sequence_data.xml',
        'security/security_payroll_overtime.xml',
        'security/ir.model.access.csv',
        'views/hr_payroll_views.xml',
    ],
}