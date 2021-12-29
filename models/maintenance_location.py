from odoo import fields, models, api


class MaintenanceLocation(models.Model):
    _name = 'maintenance.location'
    _description = 'Maintenance Location'
    _order = 'complete_name'

    _parent_store = True
    _parent_name = "parent_id"

    child_ids = fields.One2many('maintenance.location', 'parent_id', string='Child Location')
    complete_name = fields.Char(string='Complete Name', compute='_compute_complete_name', store=True)
    equipments_ids = fields.One2many(comodel_name='maintenance.equipment', inverse_name='location_id', string='Equipments')
    location_id = fields.Many2one(comodel_name='stock.location', string='Location Stock')
    location_dest_id = fields.Many2one(comodel_name='stock.location', string='Location Stock Dest')
    name = fields.Char(string='Location', index=True, required=True)
    parent_id = fields.Many2one('maintenance.location', string='Parent Location', ondelete='restrict', index=True)
    parent_path = fields.Char(index=True)
    stock_type_id = fields.Many2one(comodel_name='stock.picking.type', string='Type Operation')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for location in self:
            if location.parent_id:
                location.complete_name = '%s / %s' % (location.parent_id.complete_name, location.name)
            else:
                location.complete_name = location.name

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise models.ValidationError('Error! You cannot create recursive locations.')
