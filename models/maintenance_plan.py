from odoo import fields, models, api


class MaintenancePlan(models.Model):
    _name = 'maintenance.plan'
    _description = 'Maintenance Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Maintenance Plan', store=True)
    notes = fields.Text(string='Notes')
    document_ids = fields.One2many(comodel_name='maintenance.plan.docs', inverse_name='maintenance_plan_id')
    equipment_ids = fields.One2many(comodel_name='maintenance.equipment', inverse_name='plan_id')
    part_ids = fields.One2many(comodel_name='maintenance.plan.part', inverse_name='plan_id', store=True)


class MaintenanceEquipmentPart(models.Model):
    _name = 'maintenance.plan.part'
    _description = 'Maintenance Plan Part'

    complete_name = fields.Char(string='Complete Name', compute='_compute_complete_name', store=True)
    name = fields.Char(string='Part')
    child_ids = fields.One2many(comodel_name='maintenance.plan.part', inverse_name='parent_id', string='Child Part')
    parent_id = fields.Many2one(comodel_name='maintenance.plan.part', string='Parent Part', ondelete='restrict', index=True)
    parent_path = fields.Char(index=True)
    plan_id = fields.Many2one(comodel_name='maintenance.plan')
    task_ids = fields.One2many(comodel_name='maintenance.task', inverse_name='part_id', string='Task')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for part in self:
            if part.parent_id:
                part.complete_name = '%s / %s' % (part.parent_id.complete_name, part.name)
            else:
                part.complete_name = part.name

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise models.ValidationError('Error! You cannot create recursive part.')


class MaintenancePlanDocs(models.Model):
    _name = 'maintenance.plan.docs'
    _description = 'Maintenance Plan Docs'

    name = fields.Char(string='Name')
    file_data = fields.Binary('File')
    file_name = fields.Char('File Name')
    maintenance_plan_id = fields.Many2one(comodel_name='maintenance.plan')
