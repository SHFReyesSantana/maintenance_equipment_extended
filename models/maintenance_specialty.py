from odoo import fields, models


class MaintenanceSpecialty(models.Model):
    _name = 'maintenance.specialty'
    _description = 'Maintenance Specialty'

    name = fields.Char(string='Specialty')
    description = fields.Char(string='Description')
