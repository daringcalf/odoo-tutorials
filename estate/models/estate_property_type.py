# -*- coding: utf-8 -*-
from odoo import models, fields


class EstateProperty(models.Model):
    _name = "estate.property.type"
    _description = "Property Types"

    name = fields.Char(required=True)
