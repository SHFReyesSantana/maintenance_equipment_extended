from odoo import fields, models, api, _


class MaintenanceTask(models.Model):
    _name = 'maintenance.task'
    _description = 'Maintenance Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    document_ids = fields.One2many(comodel_name='maintenance.task.docs', inverse_name='task_id')
    duration = fields.Float(string='Duration')
    ext_maintenance = fields.Boolean(string='External Maintenance')
    name = fields.Char(string='Task')
    notes = fields.Text(string='Notes')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Supplier')
    part_id = fields.Many2one('maintenance.plan.part')
    priority = fields.Selection([('0', 'Low'), ('1', 'Medium'), ('2', 'High'), ('3', 'Very High')], string='Priority', default='0')
    predictive = fields.Selection(
        [('0', 'No measurement required.'), ('1', 'Control only minimal'), ('2', 'Control only maximum'), ('3', 'Control minimum and maximum')],
        default='0')
    process = fields.Text(string='Process')
    product_ids = fields.One2many(comodel_name='maintenance.task.product', inverse_name='task_id', auto_join=True)
    specialty_id = fields.Many2one(comodel_name='maintenance.specialty', string='Specialty')
    stop_days = fields.Integer(string='Stop Days')
    stop_hours = fields.Integer(string='Stop Hours')
    frequency = fields.Selection([('date', 'Date'), ('read', 'Read'), ('mixed', 'Mixed')], string='Frequency', default='date')
    frequency_date = fields.Selection([('0', 'Days'), ('1', 'Month')], string='Frequency Date', default='0')
    frequency_date_val = fields.Integer(string='Date Value')
    frequency_read = fields.Many2one(comodel_name='uom.uom', string='Frequency Read')
    frequency_read_val = fields.Integer(string='Read Value')
    unit = fields.Many2one(comodel_name='uom.uom', string='Unit')
    unit_min = fields.Float(string='Minimum', digits=(2, 1))
    unit_max = fields.Float(string='Maximum', digits=(2, 1))


class MaintenanceTaskDocs(models.Model):
    _name = 'maintenance.task.docs'
    _description = 'Maintenance Task Docs'

    name = fields.Char(string='Name')
    file_data = fields.Binary('File')
    file_name = fields.Char('File Name')
    task_id = fields.Many2one(comodel_name='maintenance.task')


class MaintenanceTaskProduct(models.Model):
    _name = 'maintenance.task.product'
    _description = 'Maintenance Task Product'

    name = fields.Text(string='Description')
    product_id = fields.Many2one(comodel_name='product.template', string='Product', ondelete='restrict')
    product_uom_qty = fields.Float(string='Quantity', digits=(2, 1), required=True, default=1.0)
    task_id = fields.Many2one(comodel_name='maintenance.task', string='Task Reference', required=True, ondelete='cascade', index=True, copy=False)
    uom = fields.Text(string='Units')

    @api.onchange('product_id')
    def _onchange_product(self):
        if not self.product_id:
            return
        self.write({
            'name': self.product_id.name,
            'uom': self.product_id.uom_id.name,
        })
