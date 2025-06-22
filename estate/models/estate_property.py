# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Properties"

    name = fields.Char(required=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(
        copy=False, default=fields.Date.add(fields.Date.today(), months=3)
    )
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        string="Garden Orientation",
        selection=[
            ("north", "North"),
            ("south", "South"),
            ("east", "East"),
            ("west", "West"),
        ],
        help="The orientation of the garden",
    )
    active = fields.Boolean(default=True)
    # New, Offer Received, Offer Accepted, Sold and Cancelled.
    state = fields.Selection(
        string="Status",
        selection=[
            ("new", "New"),
            ("offer_received", "Offer Received"),
            ("offer_accepted", "Offer Accepted"),
            ("sold", "Sold"),
            ("cancelled", "Cancelled"),
        ],
        default="new",
        copy=False,
        required=True,
    )

    # Relationships
    property_type_id = fields.Many2one("estate.property.type", string="Property Type")
    salesman_id = fields.Many2one(
        "res.users", string="Salesman", default=lambda self: self.env.user
    )
    buyer_id = fields.Many2one("res.partner", string="Buyer", copy=False)
    tag_ids = fields.Many2many("estate.property.tag", string="Tags")
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")

    # Computed fields
    total_area = fields.Integer(compute="_compute_total_area", string="Total Area")
    best_price = fields.Float(compute="_compute_best_price", string="Best Offer")

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for property in self:
            property.total_area = property.living_area + property.garden_area

    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        for property in self:
            property.best_price = max(property.offer_ids.mapped("price"), default=0.0)


class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Property Types"

    name = fields.Char(required=True)


class EastatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Property Tag"

    name = fields.Char(required=True)


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Property Offer"

    price = fields.Float()
    status = fields.Selection(
        string="Status",
        selection=[
            ("accepted", "Accepted"),
            ("refused", "Refused"),
        ],
        copy=False,
    )
    partner_id = fields.Many2one("res.partner", string="Partner", required=True)
    property_id = fields.Many2one("estate.property", string="Property", required=True)
