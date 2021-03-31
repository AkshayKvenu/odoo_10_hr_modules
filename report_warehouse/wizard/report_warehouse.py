# -*- coding: utf-8 -*-

from odoo import models, api, fields


class ReportWarehouse(models.TransientModel):
    _name = 'report.warehouse'

    company_id = fields.Many2one('res.company', 'Company', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=False)
    categ_id = fields.Many2one('product.category', 'Product category', required=True)
    start_date = fields.Date('Start period', required=True)
    end_date = fields.Date('End period', required=True)
    choice = fields.Selection([('all', 'All product'), ('one', 'One product')], default="all")
    line_ids = fields.One2many('report.warehouse.line', 'report_warehouse_id', 'Report warehouse line')

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            categ_id = self.env['product.product'].search([('id', '=', self.product_id.id)]).categ_id.id
            if categ_id:
                categ = self.env['product.category'].search([('id', '=', categ_id)])
                result = {'domain': {'categ_id': [('id', '=', [j.id for j in categ])]}}
                return result

    @api.onchange('choice')
    def onchange_choice(self):
        if self.choice == "all":
            categ = self.env['product.category'].search([])
            result = {'domain': {'categ_id': [('id', '=', [j.id for j in categ])]}}
            return result

    @api.multi
    def print_warehouse_report(self):
        self.ensure_one()
        if self.choice == "one":
            warehouse_obj = self.env['stock.move'].search([('company_id', '=', self.company_id.id),
                                                           ('product_id', '=', self.product_id.id),
                                                           ('product_id.categ_id', '=', self.categ_id.id),
                                                           ('date', '>=', self.start_date),
                                                           ('date', '<=', self.end_date)])
            warehouse__list = list()
            for wh in warehouse_obj:
                stock_history = self.env['stock.history'].search([('move_id', '=', wh.id)])
                quantity = 0
                for sh in stock_history:
                    quantity += sh.quantity
                warehouse_dict = {
                    'date': wh.date,
                    'picking_type_id': wh.picking_type_id,
                    'create_uid': wh.create_uid,
                    'partner_id': wh.partner_id,
                    'location_id': wh.location_id,
                    'categ_id': wh.product_id.categ_id,
                    'product_id': wh.product_id,
                    'company_id': wh.company_id,
                    'quantity': quantity,
                }
                warehouse__list += [warehouse_dict]
            self.line_ids = warehouse__list
        if self.choice == "all":
            warehouse_obj = self.env['stock.move'].search([('company_id', '=', self.company_id.id),
                                                           ('product_id.categ_id', '=', self.categ_id.id),
                                                           ('date', '>=', self.start_date),
                                                           ('date', '<=', self.end_date)])
            warehouse_list = list()
            for wh in warehouse_obj:
                stock_history = self.env['stock.history'].search([('move_id', '=', wh.id)])
                quantity = 0
                for sh in stock_history:
                    quantity += sh.quantity
                print stock_history, wh.id
                warehouse_dict = {
                    'date': wh.date,
                    'picking_type_id': wh.picking_type_id,
                    'create_uid': wh.create_uid,
                    'partner_id': wh.partner_id,
                    'location_id': wh.location_id,
                    'location_dest_id': wh.location_dest_id,
                    'categ_id': wh.product_id.categ_id,
                    'product_id': wh.product_id,
                    'company_id': wh.company_id,
                    'quantity': quantity,
                }
                warehouse_list += [warehouse_dict]
            self.line_ids = warehouse_list

    def _print_report(self, data):
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env['report'].with_context(landscape=True).get_action(records,'report_warehouse.warehouse_report', data=data)

    @api.multi
    def print_payment_report(self):
        self.ensure_one()
        data = {'ids': self.id, 'model': 'report.warehouse',
                'form': self.read(['company_id', 'product_id', 'categ_id', 'start_date', 'end_date'])[0]}
        self.print_warehouse_report()
        return self._print_report(data)


class ReportWarehouseLine(models.TransientModel):
    _name = 'report.warehouse.line'

    date = fields.Date('Operation date')
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation type')
    create_uid = fields.Many2one('res.users', 'Created by')
    partner_id = fields.Many2one('res.partner', 'Destination Address')
    location_id = fields.Many2one('stock.location', 'Source Location')
    location_dest_id = fields.Many2one('stock.location', 'Source Location')
    categ_id = fields.Many2one('product.category', 'Product category')
    product_id = fields.Many2one('product.product', 'Product')
    company_id = fields.Many2one('res.company', 'Company')
    quantity = fields.Float('Product Quantity')
    total_quantity = fields.Float('Total Quantity')
    report_warehouse_id = fields.Many2one('report.warehouse', 'Report warehouse')

