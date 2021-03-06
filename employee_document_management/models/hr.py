# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2016 Amzsys IT Solutions Pvt Ltd
#    (http://www.amzsys.com)
#    info@amzsys.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
import datetime
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api, _
from cryptography.hazmat.primitives.keywrap import aes_key_unwrap

class EmployeeDocumentType(models.Model):
    _name = 'employee.document.type'
    _description = 'Type of document'

    name = fields.Char(required=True, translate=True)
#     category = fields.Selection([('contract', 'Contract'), ('service', 'Service'), ('both', 'Both')], 'Category',
#         required=True, help='Choose wheter the service refer to contracts, services or both')

class HrEmployeeContract(models.Model):

    _name = 'hr.employee.contract'
    _description = 'Contract information for employees'
    _order = 'state desc,expiration_date'

    def compute_next_year_date(self, strdate):
        oneyear = relativedelta(years=1)
        start_date = fields.Date.from_string(strdate)
        return fields.Date.to_string(start_date + oneyear)

    name = fields.Text(compute='_compute_contract_name', store=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    cost_subtype_id = fields.Many2one('hr.document', 'Document Name', help='Cost type purchased with this cost')
    active = fields.Boolean(default=True)
    File_slect = fields.Binary(string="Select Excel File")
    filename = fields.Char()
    note = fields.Html('Note')
    date = fields.Date()
    start_date = fields.Date('Start Date', help='Date when the coverage of the contract begins')
    expiration_date = fields.Date('Expiration Date', help='Date when the coverage of the contract expirates (by default, one year after begin date)')
    days_left = fields.Integer(compute='_compute_days_left', string='Warning Date')
    purchaser_id = fields.Many2one('res.partner', 'Contractor', default=lambda self: self.env.user.partner_id.id, help='Person to which the contract is signed for')
    ins_ref = fields.Char('Invoice Reference', size=64, copy=False)
    notes = fields.Text('Terms and Conditions', help='Write here all supplementary information relative to this contract', copy=False)
    user_ids = fields.Many2many('res.users', string="Remind To")
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments")
    history_ids = fields.One2many('hr.employee.contract.history','contract_history_id')
    reminder_before = fields.Integer(string="Remind before how many days")
    next_reminder = fields.Datetime(string="Reminder Date")
    state = fields.Selection([('draft', 'Draft'), ('open', 'Valid'), ('renew', 'Near Expire'), ('expired', 'Expired'), ('closed', 'Terminated')],
                              'Status', default='draft', readonly=True, help='Choose wheter the contract is still valid or not',
                              copy=False)
    mail_time = fields.Datetime(string='Mail Send Time', readonly=True)
    document = fields.Char(string="Document #")
    
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("You can delete a record only in draft state."))
        res = super(HrEmployeeContract, self).unlink()
        return res
    
    @api.depends('employee_id', 'cost_subtype_id', 'date')
    def _compute_contract_name(self):
        for record in self:
            name = record.employee_id.name
            if name and record.date:
                name += ' / ' + record.cost_subtype_id.name + ' / ' + str(record.date)
            else:
                name = record.cost_subtype_id.name
#             if record.date:
#                 name += ' / ' + record.date
            record.name = name

    @api.depends('expiration_date', 'state')
    def _compute_days_left(self):
        """return a dict with as value for each contract an integer
        if contract is in an open state and is overdue, return 0
        if contract is in a closed state, return -1
        otherwise return the number of days before the contract expires
        """
        for record in self:
            if (record.expiration_date and record.state == 'open'):
                today = fields.Date.from_string(fields.Date.today())
                renew_date = fields.Date.from_string(record.expiration_date)
                diff_time = (renew_date - today).days
                record.days_left = diff_time > 0 and diff_time or 0
            else:
                record.days_left = -1
                
    def _action_send_expiry_mail(self):
        template = self.env.ref('employee_document_management.email_template_document_expiry_mail', False)
        if not template:
            raise UserError(_('The Forward Email Template is not in the database'))
        local_context = self.env.context.copy()
        template.with_context(local_context).send_mail(self.id, force_send=True)
        self.write({
            'state': 'expired',
            'mail_time': datetime.datetime.now()
        })
                
    def _action_send_reminder_mail(self):
        template = self.env.ref('employee_document_management.email_template_document_reminder_mail', False)
        if not template:
            raise UserError(_('The Forward Email Template is not in the database'))
        local_context = self.env.context.copy()
        template.with_context(local_context).send_mail(self.id, force_send=True)
        self.write({
            'state': 'renew',
            'mail_time': datetime.datetime.now()
        })

    @api.multi
    def action_draft(self):
        for record in self:
            if not record.expiration_date or not record.start_date:
                raise ValidationError(_("Start date and Expiration date cannot be null."))
            
            today = fields.Date.today()
#             next_reminder = datetime.datetime.strptime(record.next_reminder, '%Y-%m-%d')
            if record.expiration_date <= today:
                record._action_send_expiry_mail()
            elif record.next_reminder:
                if record.next_reminder <= today:
                    record._action_send_reminder_mail()
                else:
                    record.state = 'open'
            else:
                record.state = 'open'

    @api.multi
    def contract_close(self):
        for record in self:
            record.state = 'closed'

    @api.multi
    def contract_open(self):
        for record in self:
            record.state = 'draft'

    @api.multi
    def act_renew_contract(self):
        self.write({
            'history_ids': [(0, 0, {'start_date': self.start_date, 'expiration_date': self.expiration_date, \
                                    'next_reminder': self.next_reminder, 'date': self.date, 'ins_ref': self.ins_ref})],
            'state': 'draft', 
            'ins_ref': False, 
            'next_reminder':False, 
            'date':False, 
            'expiration_date': False,
            'start_date':False, 
            'mail_time':False,
        })
                
     
    @api.constrains('start_date', 'expiration_date')
    def _check_dates(self):
        if any(self.filtered(lambda document: document.start_date and document.expiration_date and document.start_date > document.expiration_date)):
            raise ValidationError(_("'Expiration Date' should be grater than 'Start Date'."))
        
    @api.onchange('cost_subtype_id')
    def onchange_cost_subtype_id(self):
        if self.cost_subtype_id:
            self.user_ids = self.cost_subtype_id.user_id.ids

    @api.onchange('expiration_date', 'cost_subtype_id','cost_subtype_id.reminder_before')
    def onchange_date_issue_expiry(self):
#         if any(self.filtered(lambda document: document.start_date > document.expiration_date)):
#             raise ValidationError(_("Document 'Issue Date' must be before 'Date Expiry'."))
        from_dt = fields.Date.from_string(self.start_date)
        to_dt = fields.Date.from_string(self.expiration_date)
        if from_dt and to_dt:
            time_delta = to_dt - from_dt
            if time_delta.days > self.cost_subtype_id.reminder_before:
                to_dt -= datetime.timedelta(days=self.cost_subtype_id.reminder_before)
                self.next_reminder = str(to_dt)
            else:
                self.next_reminder = str(fields.Date.today())
                 
    @api.multi
    def set_as_close(self):
        today_date = fields.Date.today()
        emp_rec = self.env['hr.employee.contract'].search([('state', 'in', ['open', 'renew'])])
        for rec in emp_rec:
            if rec.expiration_date:
                if rec.expiration_date == today_date:
                    rec._action_send_expiry_mail()

    @api.multi
    def get_partner_ids(self, user_ids):
        return str([user.partner_id.id for user in user_ids]).replace('[', '').replace(']', '') 
    
    @api.multi              
    def action_sendmail(self):
        today_date = fields.Date.today()
        print("0000000000000000sss;")
        emp_rec = self.env['hr.employee.contract'].search([('state', '=', 'open')])
        print("0000000000000000",emp_rec)
        for rec in emp_rec:
            print("111111111111")
            if rec.next_reminder:
                print("222222222222222")
                dt = datetime.datetime.strptime(str(rec.next_reminder), '%Y-%m-%d %H:%M:%S')
                if dt.date() == today_date:
                    print("3333333333333")
                    rec._action_send_reminder_mail()
 
    
class Employee(models.Model):
    _inherit = 'hr.employee'
     
    working_status = fields.Selection([('presently_working', 'Presently Working'), ('on_vacation', 'On Vacation'), ('resigned', 'Resigned'), ('terminated', 'Terminated')], default='presently_working', string='Working Status')
    joining_date = fields.Date(string='Joining Date')
    log_contracts = fields.One2many('hr.employee.contract', 'employee_id', 'Documents')
    contract_count = fields.Integer(compute="_compute_count_all", string='Documents')
    contract_renewal_due_soon = fields.Boolean(compute='_compute_contract_reminder', search='_search_contract_renewal_due_soon', string='Has Documents to renew', multi='document_info')
    contract_renewal_overdue = fields.Boolean(compute='_compute_contract_reminder', search='_search_get_overdue_contract_reminder', string='Has Document Overdue', multi='document_info')
    contract_renewal_name = fields.Text(compute='_compute_contract_reminder', string='Name of document to renew soon', multi='document_info')
    contract_renewal_total = fields.Text(compute='_compute_contract_reminder', string='Total of documents due or overdue minus one', multi='document_info')
    
    def _compute_count_all(self):
        LogContract = self.env['hr.employee.contract']
        for record in self:
            record.contract_count = LogContract.search_count([('employee_id', '=', record.id)])

    @api.depends('log_contracts')
    def _compute_contract_reminder(self):
        for record in self:
            overdue = False
            due_soon = False
            total = 0
            name = ''
            for element in record.log_contracts:
                if element.state in ('open') and element.expiration_date:
                    current_date_str = fields.Date.context_today(record)
                    due_time_str = element.expiration_date
                    current_date = fields.Date.from_string(current_date_str)
                    due_time = fields.Date.from_string(due_time_str)
                    diff_time = (due_time - current_date).days
                    if diff_time < 0:
                        overdue = True
                        total += 1
                    if diff_time < 15 and diff_time >= 0:
                            due_soon = True
                            total += 1
                    if overdue or due_soon:
                        log_contract = self.env['hr.employee.contract'].search([('employee_id', '=', record.id), ('state', '=', 'open')],
                            limit=1, order='expiration_date asc')
                        if log_contract:
                            # we display only the name of the oldest overdue/due soon contract
                            name = log_contract.cost_subtype_id.name

            record.contract_renewal_overdue = overdue
            record.contract_renewal_due_soon = due_soon
            record.contract_renewal_total = total - 1  # we remove 1 from the real total for display purposes
            record.contract_renewal_name = name
            
    def _search_contract_renewal_due_soon(self, operator, value):
        res = []
        assert operator in ('=', '!=', '<>') and value in (True, False), 'Operation not supported'
        if (operator == '=' and value is True) or (operator in ('<>', '!=') and value is False):
            search_operator = 'in'
        else:
            search_operator = 'not in'
        today = fields.Date.context_today(self)
        datetime_today = fields.Datetime.from_string(today)
        limit_date = fields.Datetime.to_string(datetime_today + relativedelta(days=+15))
        self.env.cr.execute("""SELECT employee_id,
                        count(id) AS contract_number
                        FROM hr_employee_contract contract
                        WHERE contract.expiration_date IS NOT NULL
                          AND contract.expiration_date > %s
                          AND contract.expiration_date < %s
                          AND contract.state IN ('open')
                        GROUP BY employee_id""", (today, limit_date))
        res_ids = [x[0] for x in self.env.cr.fetchall()]
        res.append(('id', search_operator, res_ids))
        return res

    def _search_get_overdue_contract_reminder(self, operator, value):
        res = []
        assert operator in ('=', '!=', '<>') and value in (True, False), 'Operation not supported'
        if (operator == '=' and value is True) or (operator in ('<>', '!=') and value is False):
            search_operator = 'in'
        else:
            search_operator = 'not in'
        today = fields.Date.context_today(self)
        self.env.cr.execute('''SELECT employee_id,
                        count(id) AS contract_number
                        FROM hr_employee_contract contract
                        WHERE contract.expiration_date IS NOT NULL
                          AND contract.expiration_date < %s
                          AND contract.state IN ('open', 'expired')
                        GROUP BY employee_id ''', (today,))
        res_ids = [x[0] for x in self.env.cr.fetchall()]
        res.append(('id', search_operator, res_ids))
        return res
    
    @api.multi
    def return_action_to_open(self):
        """ This opens the xml view specified in xml_id for the current vehicle """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('employee_document_management', xml_id)
            res.update(
                context=dict(self.env.context, default_employee_id=self.id, group_by=False),
                domain=[('employee_id', '=', self.id)]
            )
            return res
        return False
    
class EmployeeDocument(models.Model):
    _name = "hr.document"

    name = fields.Char(string='Document Name')
    user_id = fields.Many2many('res.users', string='Responsible')
    reminder_before = fields.Integer(string='Remind Before How many days')
    
class HrEmployeeContractHistory(models.Model):
    _name = "hr.employee.contract.history"
    contract_history_id = fields.Many2one('hr.employee.contract')
    
    start_date = fields.Date('Start Date')
    expiration_date = fields.Date('Expiration Date')
    next_reminder = fields.Datetime(string="Reminder Date")
    date = fields.Date("Invoice Date")
    ins_ref = fields.Char('Invoice Reference')
    
 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
