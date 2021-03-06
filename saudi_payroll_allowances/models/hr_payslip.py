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

from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError

from datetime import date, datetime, time, timedelta
from dateutil import relativedelta
from pytz import timezone

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    duration = fields.Integer(string='Working Duration',readonly=True)
    
    def get_lines_by_contribution_register(self):
        payslip_lines = self.mapped('details_by_salary_rule_category').filtered(lambda r: r.appears_on_payslip)
        result = {}
        res = {}
        for line in payslip_lines.filtered('register_id'):
            result.setdefault(line.slip_id.id, {})
            result[line.slip_id.id].setdefault(line.register_id, line)
            result[line.slip_id.id][line.register_id] |= line
        for payslip_id, lines_dict in result.items():
            res.setdefault(payslip_id, [])
            for register, lines in lines_dict.items():
#                 res[payslip_id].append({
#                     'register_name': register.name,
#                     'total': sum(lines.mapped('total')),
#                 })
                for line in lines:
                    res[payslip_id].append({
                        'name': line.name,
                        'code': line.code,
                        'quantity': line.quantity,
                        'amount': line.amount,
                        'total': line.total,
                    })
        return res
    
    @api.model
    def create(self, vals):
        result = super(HrPayslip, self).create(vals)
        if result.employee_id.joining_date and result.employee_id.joining_date < result.date_to:
            date_to = datetime.strptime(str(result.date_to), '%Y-%m-%d')
            joining_date = datetime.strptime(str(result.employee_id.joining_date), '%Y-%m-%d')
            relative_duration = relativedelta.relativedelta(date_to, joining_date)
            duration = relative_duration.months + (12 * relative_duration.years)
            result.duration = duration
        return result
    
    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        res = super(HrPayslip, self).get_worked_day_lines(contract_ids, date_from, date_to)
            
        for contract in self.env['hr.contract'].browse(contract_ids).filtered(lambda contract: contract.working_hours):
            employee_join_date = False
            if contract.employee_id.joining_date:
                employee_join_date = datetime.strptime(contract.employee_id.joining_date, '%Y-%m-%d')
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            if not self:
                employee_join_date = datetime.combine(fields.Date.from_string(contract.employee_id.joining_date), time.min)
            if employee_join_date and date_from < employee_join_date < date_to:
                print(date_from,date_to)
                join_date = employee_join_date.date()
                join = {
                    'name': _("Employee Joining on  %s" % str(join_date)),
                    'sequence': 3,
                    'code': 'join',
                    'number_of_days': join_date.day - 1,
                    'contract_id': contract.id,
                }
                res.append(join)
        return res
    
    
    
    @api.multi
    def write(self, vals):
        employee_id = 'employee_id' in vals and vals['employee_id'] or self.employee_id.id
        date_to_str = 'date_to' in vals and vals['date_to'] or str(self.date_to)
        date_from_str = 'date_from' in vals and vals['date_from'] or str(self.date_from)
        employee = self.env['hr.employee'].browse(employee_id)
        if employee.joining_date:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            joining_date = datetime.strptime(str(employee.joining_date), '%Y-%m-%d')
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
            
            if joining_date < date_to:
                relative_duration = relativedelta.relativedelta(date_to, joining_date)
                duration = relative_duration.months + (12 * relative_duration.years)
                vals['duration'] = duration
        result = super(HrPayslip, self).write(vals)
        return result
    

                
    @api.multi
    def send_email_multi_payslips(self):
        template = self.env.ref('saudi_payroll_allowances.email_template_payslip_confirmation_ml', False)
        for record in self:
            if record.employee_id.work_email:
                self.env['mail.template'].browse(template.id).send_mail(record.id, force_send=True)
        
class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    @api.model
    def default_get(self, field_list):
        res = super(HrPayrollStructure, self).default_get(field_list)
        res.update({'parent_id': False})
        return res
    
    
class HrPayrollRun(models.Model):
    _inherit = 'hr.payslip.run'
     
    company_id = fields.Many2one('res.company','Company',default = lambda self: self.env.user.company_id)
   
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
