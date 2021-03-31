# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Warehouse report',
    'author': 'Parfait AllA',
    'version': '8.0',
    'sequence': 3,
    'category': 'Warehouse',
    'description': """
        This module is use for inventory report.
    """,
    'website': "https://github.com/allan225",
    'depends': ['stock'],
    'data': [
        "wizard/report_warehouse_view.xml",
        "report/warehouse_report.xml",
        "report/report.xml",
    ],
    "images": [
            'static/description/banner.png'
        ],
    'installable': True,
    'application': True,
}
