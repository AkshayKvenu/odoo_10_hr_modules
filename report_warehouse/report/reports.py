# -*- coding: utf-8 -*-

from odoo import models, api


class PrintReport(models.AbstractModel):
    _name = 'report.report_warehouse.warehouse_report'

    @api.model
    def render_html(self, docids, data=None):
        self.model = data['model']
        docs = self.env[self.model].browse(data['ids'])
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('report_warehouse.warehouse_report', docargs)
