import json
from datetime import datetime, timedelta

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

COLORS = [
    (1, "#777777"),
    (2, "#F06050"),
    (3, "#F4A460"),
    (4, "#F7CD1F"),
    (5, "#6CC1ED"),
    (6, "#814968"),
    (7, "#EB7E7F"),
    (8, "#2C8397"),
    (9, "#475577"),
]


def next_request(frequency_date, frequency_date_val):
    if frequency_date == '1':
        date_next_request = (datetime.now() + timedelta(days=(frequency_date_val * 30)))
    else:
        date_next_request = (datetime.now() + timedelta(days=frequency_date_val))
    return date_next_request


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    active = fields.Boolean(default=True)
    attachment_number = fields.Integer(string='Number of Attachments', compute='_compute_attachment_number')
    code = fields.Char(string='Code', required=True, readonly=True, default='New', copy=False)
    schedule_date_end = fields.Datetime(string='Date End')
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')
    frequency = fields.Char(string='Frequency')
    maintenance_type = fields.Selection(selection_add=[("predictive", "Predictive")])
    notes = fields.Text(string='Notes')
    picking_ids = fields.One2many(comodel_name='stock.picking', inverse_name='request_id', string='Transfers')
    products_ids = fields.Many2many('maintenance.task.product', string='Products')
    process = fields.Text(string='Process')
    request_docs_ids = fields.Many2many('maintenance.task.docs', string='Documents')
    specialty = fields.Char(string='Specialty')
    uom_id = fields.Many2one(comodel_name='uom.uom', string='Unit Measure Predictive')
    uom_val = fields.Float(string="Units")
    duration_request = fields.Float(string='Durations', store=True)
    duration_request_date = fields.Char(compute='_compute_date_request')
    default_group_1 = fields.Char(string='JSON', compute="_default_group_1")
    color_request = fields.Char(string='Color Json', compute="_default_colors")
    stage_id_id = fields.Integer(related='stage_id.id')

    _sql_constraints = [
        ('code_unique',
         'UNIQUE(code)',
         "The code number must be unique"),
    ]

    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('maintenance.request') or '/'
        return super(MaintenanceRequest, self).create(vals)

    @api.onchange('schedule_date', 'duration')
    def _onchange_schedule_date(self):
        if self.schedule_date and self.duration:
            self.schedule_date_end = (self.schedule_date + timedelta(hours=self.duration))

    @api.depends('duration')
    def _compute_date_request(self):
        for time in self:
            td = timedelta(hours=time.duration)
            time.duration_request_date = datetime.strftime((datetime(1, 1, 1, 0, 0) + td), '%I:%M')

    def _compute_picking_ids(self):
        order = self.env['stock.picking'].search([('origin', '=', self.code)])
        self.picking_ids = order
        self.delivery_count = len(order)

    def action_view_delivery(self):
        stock = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            stock['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in stock:
                stock['views'] = form_view + [(state, view) for state, view in stock['views'] if view != 'form']
            else:
                stock['views'] = form_view
            stock['res_id'] = pickings.id
        picking_id = pickings.filtered(lambda l: l.picking_type_id.code == 'outgoing')
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        stock['context'] = dict(self._context, default_picking_type_id=picking_id.picking_type_id.id, default_origin=self.name,
            default_group_id=picking_id.group_id.id)
        return stock

    def get_directory(self):
        directory = self.env.ref('maintenance_equipment_extended.directory_maintenance_request')
        domain = [("is_hidden", "=", False), ("parent_id", "=", directory.id), ("name", "=", self.code)]
        folder = self.env["dms.directory"].search(domain)
        return folder

    def _compute_attachment_number(self):
        folder = self.get_directory()
        model = self.env["dms.file"].search([('directory_id', '=', folder.id)])
        for record in self:
            record.attachment_number = len(model)

    def action_get_attachment_view(self):
        directory = self.env.ref('maintenance_equipment_extended.directory_maintenance_request')
        folder = self.get_directory()
        if not folder:
            folder = self.create_folder(self.code, directory.id)
        res = self.env['ir.actions.act_window'].for_xml_id('dms', 'action_dms_files_directory')
        res['context'] = {'default_directory_id': folder.id, 'searchpanel_default_directory_id': folder.id}
        return res

    def create_folder(self, code, directory):
        vals = {
            'name': code,
            'parent_id': directory,
        }
        return self.env['dms.directory'].create(vals)

    def measure_predictive(self):
        pass

    @api.onchange('stage_id')
    def _onchange_stage(self):
        if self.stage_id.done:
            if self.uom_id:
                if self.uom_val > 0:
                    self.write_measure()
                else:
                    raise ValidationError(_("Error in value of measure predictive"))
                self.write_stage()

    def write_measure(self):
        for measure in self.equipment_id.equipment_measure_ids:
            if measure.uom_id.id == self.uom_id.id:
                measure.write({
                    'value': self.uom_val,
                })
                user = self.env.user.login
                body = "Measure update for\n User: %s\n Measure: %s\n Value: %s" % (user, self.uom_id.name, self.uom_val)
                self.equipment_id.message_post(body=body)
            else:
                pass

    def write_stage(self):
        for request in self.equipment_id.equipment_line_ids:
            if request.request == self.code:
                request.write({'date_execution': self.close_date})
                if request.frequency != 'read':
                    date = next_request(request.frequency_date, request.frequency_date_val)
                    request.write({'date_next_request': date})

    def _default_group_1(self):
        for request in self:
            links = []
            json_obj = {
                'id': request.equipment_id.id,
                'content': request.equipment_id.name,
                'treeLevel': 1,
                'nestedGroups': request.maintenance_type,
            }
            links.append(json_obj)
            request.default_group_1 = json.dumps(links)

    def _default_colors(self):
        for request in self:
            color = []
            json_obj = {
                'color': COLORS[request.stage_id.color - 1],
                'field': 'stage_id_id',
                'opt': '==',
                'value': request.stage_id.id,
            }
            color.append(json_obj)
            request.color_request = json.dumps(color)


