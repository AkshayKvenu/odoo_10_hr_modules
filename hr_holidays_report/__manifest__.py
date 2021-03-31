# -*- coding: utf-8 -*-
{
    'name': "hr_holidays_report",

    'summary': """
        Module for Leave report""",

    'description': """
        Module for Leave report
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1.20.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_holidays'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/leave_report.xml',
    ],
}