# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
    
    l10n_bd_fiscal_year = fields.Char(
        string='Fiscal Year',
        compute='_compute_fiscal_year',
        store=True,
        help='Fiscal year (July-June)'
    )
    
    l10n_bd_allocation_source = fields.Selection([
        ('annual', 'Annual Entitlement'),
        ('carryover', 'Carryover from Previous Year'),
        ('bonus', 'Bonus/Special Allocation'),
        ('adjustment', 'Manual Adjustment'),
    ], string='Allocation Source', default='annual')

    @api.depends('date_from')
    def _compute_fiscal_year(self):
        for allocation in self:
            if allocation.date_from:
                year = allocation.date_from.year
                month = allocation.date_from.month
                if month >= 7:
                    allocation.l10n_bd_fiscal_year = f"{year}-{year + 1}"
                else:
                    allocation.l10n_bd_fiscal_year = f"{year - 1}-{year}"
            else:
                allocation.l10n_bd_fiscal_year = False