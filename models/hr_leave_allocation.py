# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
    
    l10n_bd_is_carryover = fields.Boolean(
        string='Is Carryover',
        default=False,
        help='Indicates this allocation is a carryover from previous year'
    )
    
    l10n_bd_carryover_from_year = fields.Integer(
        string='Carried Over From Year',
        help='The year from which these days were carried over'
    )
    
    l10n_bd_carryover_expiry_date = fields.Date(
        string='Carryover Expiry Date',
        help='Date when this carryover allocation expires'
    )

    @api.constrains('number_of_days', 'holiday_status_id', 'employee_id')
    def _check_max_days_per_year(self):
        """Validate allocation against max days per year limit"""
        for allocation in self: 
            leave_type = allocation.holiday_status_id
            
            # Skip carryover allocations from this check
            if allocation.l10n_bd_is_carryover:
                continue
            
            # Skip if no max days limit is set
            if not leave_type.l10n_bd_max_days_per_year or leave_type.l10n_bd_max_days_per_year <= 0:
                continue
            
            max_days = leave_type.l10n_bd_max_days_per_year
            
            # Get allocation year
            current_year = date.today().year
            if allocation.date_from: 
                current_year = allocation.date_from.year
            
            # Calculate total allocated days for this employee, leave type, and year (excluding carryovers)
            domain = [
                ('employee_id', '=', allocation.employee_id.id),
                ('holiday_status_id', '=', leave_type.id),
                ('state', 'in', ['confirm', 'validate1', 'validate']),
                ('l10n_bd_is_carryover', '=', False),
            ]
            
            # Exclude current allocation if it's being updated
            if allocation.id:
                domain.append(('id', '!=', allocation.id))
            
            other_allocations = self.search(domain)
            
            # Filter by year
            total_other_days = sum(
                alloc.number_of_days for alloc in other_allocations
                if alloc.date_from and alloc.date_from.year == current_year
            )
            
            total_days = total_other_days + allocation.number_of_days
            
            if total_days > max_days:
                raise ValidationError(
                    _('Cannot allocate %(days)s days for "%(leave_type)s".'
                      'Maximum allowed per year is %(max)s days. '
                      'Employee "%(employee)s" already has %(existing)s days allocated for %(year)s.') % {
                        'days': allocation.number_of_days,
                        'leave_type': leave_type.name,
                        'max': max_days,
                        'employee': allocation.employee_id.name,
                        'existing': total_other_days,
                        'year': current_year,
                    }
                )

    @api.model
    def _cron_expire_carryover_allocations(self):
        """Cron job to expire carryover allocations"""
        today = date.today()
        
        expired_allocations = self.search([
            ('l10n_bd_is_carryover', '=', True),
            ('l10n_bd_carryover_expiry_date', '!=', False),
            ('l10n_bd_carryover_expiry_date', '<', today),
            ('state', '=', 'validate'),
        ])
        
        for allocation in expired_allocations: 
            # Calculate remaining days
            remaining = allocation.number_of_days - allocation.leaves_taken
            
            if remaining > 0:
                # Reduce the allocation to only the taken days
                allocation.sudo().write({
                    'number_of_days': allocation.leaves_taken,
                })
                
                # Post a message
                allocation.message_post(
                    body=_('Carryover allocation expired. %(remaining)s unused days have been forfeited.') % {
                        'remaining': remaining,
                    }
                )

    @api.model
    def process_year_end_carryover(self, year=None):
        """
        Process year-end carryover for all employees and leave types.
        Call this method via cron job or manual action at year end.
        """
        if not year:
            year = date.today().year - 1  # Process previous year by default
        
        # Get all leave types with carryover enabled
        leave_types = self.env['hr.leave.type'].search([
            ('l10n_bd_carryover_allowed', '=', True),
        ])
        
        if not leave_types:
            return {'processed': 0, 'message': _('No leave types with carryover enabled.')}
        
        # Get all employees
        employees = self.env['hr.employee'].search([('active', '=', True)])
        
        processed_count = 0
        carryover_details = []
        
        for employee in employees:
            for leave_type in leave_types: 
                result = self._create_carryover_allocation(employee, leave_type, year)
                if result: 
                    processed_count += 1
                    carryover_details.append(result)
        
        return {
            'processed': processed_count,
            'details': carryover_details,
            'message': _('Processed %(count)s carryover allocations.') % {'count': processed_count}
        }

    @api.model
    def _create_carryover_allocation(self, employee, leave_type, from_year):
        """Create carryover allocation for a single employee and leave type"""
        
        # Calculate unused days from the previous year
        year_start = date(from_year, 1, 1)
        year_end = date(from_year, 12, 31)
        
        # Get allocations for the year
        allocations = self.search([
            ('employee_id', '=', employee.id),
            ('holiday_status_id', '=', leave_type.id),
            ('state', '=', 'validate'),
            ('date_from', '>=', year_start),
            ('date_from', '<=', year_end),
        ])
        
        if not allocations:
            return None
        
        # Calculate total allocated and taken
        total_allocated = sum(allocations.mapped('number_of_days'))
        
        # Get leaves taken in that year
        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('holiday_status_id', '=', leave_type.id),
            ('state', '=', 'validate'),
            ('request_date_from', '>=', year_start),
            ('request_date_from', '<=', year_end),
        ])
        
        total_taken = sum(leaves.mapped('number_of_days'))
        unused_days = total_allocated - total_taken
        
        if unused_days <= 0:
            return None
        
        # Apply carryover max days limit
        max_carryover = leave_type.l10n_bd_carryover_max_days
        if max_carryover and max_carryover > 0:
            unused_days = min(unused_days, max_carryover)
        
        # Calculate expiry date
        new_year_start = date(from_year + 1, 1, 1)
        expiry_date = None
        
        if leave_type.l10n_bd_carryover_expiry_months and leave_type.l10n_bd_carryover_expiry_months > 0:
            expiry_date = new_year_start + relativedelta(months=leave_type.l10n_bd_carryover_expiry_months)
        
        # Check if carryover allocation already exists
        existing_carryover = self.search([
            ('employee_id', '=', employee.id),
            ('holiday_status_id', '=', leave_type.id),
            ('l10n_bd_is_carryover', '=', True),
            ('l10n_bd_carryover_from_year', '=', from_year),
        ], limit=1)
        
        if existing_carryover: 
            return None  # Already processed
        
        # Create carryover allocation
        carryover_allocation = self.create({
            'name': _('Carryover from %(year)s - %(leave_type)s') % {
                'year': from_year,
                'leave_type': leave_type.name,
            },
            'holiday_status_id': leave_type.id,
            'employee_id': employee.id,
            'number_of_days': unused_days,
            'date_from': new_year_start,
            'date_to': expiry_date,
            'l10n_bd_is_carryover':  True,
            'l10n_bd_carryover_from_year': from_year,
            'l10n_bd_carryover_expiry_date':  expiry_date,
            'allocation_type': 'regular',
        })
        
        # Auto-approve the carryover allocation
        carryover_allocation.action_validate()
        
        return {
            'employee': employee.name,
            'leave_type': leave_type.name,
            'days':  unused_days,
            'expiry_date': expiry_date,
        }