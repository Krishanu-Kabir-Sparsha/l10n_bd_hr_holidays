# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class HrLeaveCarryoverWizard(models.TransientModel):
    _name = 'hr.leave.carryover.wizard'
    _description = 'Leave Carryover Wizard'
    
    year = fields.Integer(
        string='Process Carryover For Year',
        required=True,
        default=lambda self: date.today().year - 1
    )
    
    leave_type_ids = fields.Many2many(
        'hr.leave.type',
        string='Leave Types',
        domain="[('l10n_bd_carryover_allowed', '=', True)]",
        help='Leave blank to process all leave types with carryover enabled'
    )
    
    employee_ids = fields.Many2many(
        'hr.employee',
        string='Employees',
        help='Leave blank to process all active employees'
    )
    
    result_message = fields.Text(
        string='Result',
        readonly=True
    )

    def action_process_carryover(self):
        """Process carryover based on wizard selections"""
        self.ensure_one()
        
        Allocation = self.env['hr.leave.allocation']
        
        # Get leave types
        leave_types = self.leave_type_ids
        if not leave_types:
            leave_types = self.env['hr.leave.type'].search([
                ('l10n_bd_carryover_allowed', '=', True),
            ])
        
        if not leave_types: 
            raise UserError(_('No leave types with carryover enabled found.'))
        
        # Get employees
        employees = self.employee_ids
        if not employees: 
            employees = self.env['hr.employee'].search([('active', '=', True)])
        
        processed_count = 0
        details = []
        
        for employee in employees:
            for leave_type in leave_types:
                result = Allocation._create_carryover_allocation(employee, leave_type, self.year)
                if result:
                    processed_count += 1
                    details.append(
                        _('%(employee)s: %(days)s days of %(leave_type)s (expires: %(expiry)s)') % {
                            'employee': result['employee'],
                            'days': result['days'],
                            'leave_type': result['leave_type'],
                            'expiry': result['expiry_date'] or _('Never'),
                        }
                    )
        
        if processed_count == 0:
            result_message = _('No carryover allocations created. Either no unused days found or carryover already processed.')
        else:
            result_message = _('Successfully created %(count)s carryover allocations:\n\n%(details)s') % {
                'count': processed_count,
                'details': '\n'.join(details),
            }
        
        self.result_message = result_message
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.carryover.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target':  'new',
        }

    @api.model
    def process_carryover_for_type(self, leave_type):
        """Called from leave type action button"""
        return {
            'name': _('Process Carryover'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.carryover.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_leave_type_ids': [(6, 0, [leave_type.id])],
                'default_year': date.today().year - 1,
            }
        }