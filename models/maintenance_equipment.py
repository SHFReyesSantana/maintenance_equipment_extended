from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    equipment_line_ids = fields.One2many(comodel_name='maintenance.equipment.line', inverse_name='equipment_id')
    equipment_measure_ids = fields.One2many(comodel_name='maintenance.equipment.measure', inverse_name='equipment_id')
    location_id = fields.Many2one(comodel_name='maintenance.location', string='Location Equipment')
    part_count = fields.Integer(string='Count', compute='_compute_part_count')
    plan_id = fields.Many2one(comodel_name='maintenance.plan', string='Plan')
    purchase_number = fields.Integer(string='Number of Purchase', compute='_compute_count_po')

    def _compute_part_count(self):
        for equipment in self:
            equipment.part_count = len(equipment.plan_id.part_ids)

    @api.onchange('plan_id')
    def _onchange_plan_name(self):
        if self.equipment_line_ids.request:
            raise ValidationError(_("The Equipment %s have task") % self.name)
        else:
            lines = []
            parts = self.env['maintenance.task'].search([('part_id.plan_id', '=', self.plan_id.id)])
            for part in parts:
                vals = {
                    'duration': part.duration,
                    'ext_maintenance': True if part.ext_maintenance else False,
                    'frequency': part.frequency,
                    'frequency_date': part.frequency_date,
                    'frequency_date_val': part.frequency_date_val,
                    'frequency_read': part.frequency_read,
                    'frequency_read_val': part.frequency_read_val,
                    'partner_id': part.partner_id.id,
                    'part': part.part_id.complete_name,
                    'priority': part.priority,
                    'predictive': part.predictive,
                    'maintenance_team_id': part.maintenance_team_id,
                    'stop_days': part.stop_days,
                    'stop_hours': part.stop_hours,
                    'task_id': part.id,
                    'unit': part.unit,
                    'unit_min': part.unit_min,
                    'unit_max': part.unit_max,
                }
                lines.append((0, 0, vals))
            self.write({
                'equipment_line_ids': lines,
            })

    def _compute_count_po(self):
        res = self.env['purchase.order'].search([('origin', '=', self.id)])
        for record in self:
            record.purchase_number = len(res)

    def action_view_po(self):
        res = self.env['ir.actions.act_window'].for_xml_id('purchase', 'purchase_rfq')
        res['domain'] = [('origin', '=', self.id)]
        return res

    def create_measure(self, uom):
        vals = []
        measures = self.equipment_measure_ids
        if measures:
            for measure in measures:
                if measure.uom_id.id == uom:
                    return
                else:
                    line = {
                        'uom_id': uom,
                    }
                    vals.append((0, 0, line))
                    self.update({
                        'equipment_measure_ids': vals,
                    })
        else:
            line = {
                'uom_id': uom,
            }
            vals.append((0, 0, line))
            self.update({
                'equipment_measure_ids': vals,
            })

    def create_next_request(self):
        for line in self.equipment_line_ids:
            if line.date_next_request == fields.Date.now():
                line.create_request()
            if line.frequency in ('read', 'mixed'):
                if self.equipment_measure_ids:
                    for measure in self.equipment_measure_ids:
                        if line.frequency_read_val >= measure.value:
                            line.create_request()

    def update_request(self):
        request = self.env['maintenance.request'].search([('active', '=', False)])
        for task in request:
            for line in self.equipment_line_ids:
                if line.request == task.code:
                    vals = {
                        'request': False,
                        'date_application': False,
                    }
                    line.update(vals)


class MaintenanceEquipmentLine(models.Model):
    _name = 'maintenance.equipment.line'
    _description = 'Maintenance Equipment Line'

    date_application = fields.Char(string='Date Start')
    date_execution = fields.Date(string='Date Finish')
    date_next_request = fields.Date(string='Date Next Request')
    duration = fields.Float(string='Duration')
    equipment_id = fields.Many2one(comodel_name='maintenance.equipment')
    ext_maintenance = fields.Boolean(string='External Maintenance')
    frequency = fields.Selection([('date', 'Date'), ('read', 'Read'), ('mixed', 'Mixed')], default='date')
    frequency_date = fields.Selection([('0', 'Days'), ('1', 'Month')], string='Frequency Date', default='0')
    frequency_date_val = fields.Integer(string='Date Value')
    frequency_read = fields.Many2one(comodel_name='uom.uom', string='Frequency Read')
    frequency_read_val = fields.Integer(string='Read Value')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Supplier')
    part = fields.Char(string='Part')
    priority = fields.Selection([('0', 'Low'), ('1', 'Medium'), ('2', 'High'), ('3', 'Very High')], string='Priority', default='0')
    predictive = fields.Selection(
        [('0', 'No measurement required.'), ('1', 'Control only minimal'), ('2', 'Control only maximum'), ('3', 'Control minimum and maximum')],
        default='0')
    process = fields.Text(string='Process')
    request = fields.Char(string='Request')
    maintenance_team_id = fields.Many2one(comodel_name='maintenance.team', string='Maintenance Team')
    stop_days = fields.Integer(string='Stop Days')
    stop_hours = fields.Integer(string='Stop Hours')
    task_id = fields.Many2one(comodel_name='maintenance.task')
    unit = fields.Many2one(comodel_name='uom.uom', string='Unit')
    unit_min = fields.Float(string='Minimum', digits=(2, 1))
    unit_max = fields.Float(string='Maximum', digits=(2, 1))

    def number_request(self):
        if self.equipment_id.location_id.id:
            if self.ext_maintenance:
                self.create_purchase_request()
            else:
                if self.frequency != 'date':
                    self.equipment_id.create_measure(self.frequency_read.id)
                number = self.create_request()
                self.update({
                    'request': number.code,
                    'date_application': number.request_date,
                })
                if len(number.products_ids) > 0:
                    stock = self.create_stock(number)
                    stock.action_confirm()
                    stock.action_assign()
        else:
            raise ValidationError(_("The Equipment %s have not physical location") % self.equipment_id.name)

    def create_request(self):
        vals = {
            'duration': self.duration,
            'equipment_id': self.equipment_id.id,
            'frequency': (str(self.frequency_date_val) + ' ' + (
                'Days' if self.frequency_date == '0' else 'Months')) if self.frequency == 'date' else (
                    str(self.frequency_read_val) + ' ' + str(self.frequency_read.name)) if self.frequency == 'read' else (
                    str(self.frequency_date_val) + ' ' + ('Days' if self.frequency_date == '0' else 'Months') + '-- Or Every --' + str(
                self.frequency_read_val) + ' ' + str(self.frequency_read.name)),
            'name': self.part,
            'notes': self.task_id.notes,
            'priority': self.priority,
            'process': self.task_id.process,
            'products_ids': self.task_id.product_ids,
            'request_docs_ids': self.task_id.document_ids,
            'maintenance_team_id': self.maintenance_team_id.id,
            'maintenance_type': 'predictive' if self.unit else 'preventive',
            'uom_id': self.unit.id if self.unit else False
        }
        number = self.env['maintenance.request'].create(vals)
        return number

    def create_stock(self, number):
        lines = []
        for product in number.products_ids:
            line = {
                'name': product.product_id.name,
                'product_id': product.product_id,
                'product_uom': product.product_id.uom_id,
                'product_uom_qty': product.product_uom_qty,
            }
            lines.append((0, 0, line))
        vals = {
            'scheduled_date': number.request_date,
            'origin': number.code,
            'picking_type_id': self.equipment_id.location_id.stock_type_id.id,
            'location_id': self.equipment_id.location_id.location_id.id,
            'location_dest_id': self.equipment_id.location_id.location_dest_id.id,
            'move_ids_without_package': lines,
        }
        stock = self.env['stock.picking'].create(vals)
        return stock

    def create_purchase_request(self):
        product = self.env["product.product"].search(
            [('product_tmpl_id', '=', self.env.ref('maintenance_equipment_extended.maintenance_product_product').id)])
        lines = []
        line = {
            'product_id': product.id,
            'name': self.part + " _ " + self.task_id.name,
            'date_planned': fields.Date.today(),
            'price_unit': product.lst_price,
            'product_qty': 1,
            'product_uom': product.uom_id.id,
        }
        lines.append((0, 0, line))
        vals = {
            'partner_id': self.partner_id.id,
            'order_line': lines,
            'origin': self.equipment_id.id,
        }
        self.env['purchase.order'].create(vals)


class MaintenanceEquipmentMeasure(models.Model):
    _name = 'maintenance.equipment.measure'
    _description = 'Maintenance Equipment Measure'

    equipment_id = fields.Many2one(comodel_name='maintenance.equipment')
    uom_id = fields.Many2one(comodel_name='uom.uom', string='Unit')
    value = fields.Integer(string='Value', tracking=True)
