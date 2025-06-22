# -*- coding: utf-8 -*-
from odoo import models, fields, api
from exceptions import UserError


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

    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = "north"
        else:
            self.garden_area = 0
            self.garden_orientation = None

    # Actions
    def action_set_property_sold(self):
        for property in self:
            if property.state == "cancelled":
                raise UserError("cancelled properties cannot be sold")
            property.state = "sold"

    def action_set_property_cancelled(self):
        for property in self:
            if property.state == "sold":
                raise UserError("sold properties cannot be cancelled")
            property.state = "cancelled"

    # Constraints
    _sql_constraints = [
        (
            "check_expected_price_strictly_positive",
            "CHECK(expected_price > 0)",
            "The expected price must be strictly positive.",
        ),
        (
            "check_selling_price_positive",
            "CHECK(selling_price >= 0)",
            "The selling price must be positive.",
        ),
    ]


class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Property Types"

    name = fields.Char(required=True)


class EastatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Property Tag"

    name = fields.Char(required=True)

    # Constraints
    _sql_constraints = [
        (
            "check_name_unique",
            "unique(name)",
            "The tag name must be unique.",
        )
    ]


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
    validity = fields.Integer(
        string="Validity (days)",
        default=7,
        help="Number of days the offer is valid",
    )

    # Computed fields
    date_deadline = fields.Date(
        compute="_compute_date_deadline",
        string="Deadline",
        inverse="_inverse_date_deadline",
    )

    @api.depends("validity")
    def _compute_date_deadline(self):
        for offer in self:
            offer.date_deadline = fields.Date.add(
                offer.create_date.date() if offer.create_date else fields.Date.today(),
                days=offer.validity,
            )

    def _inverse_date_deadline(self):
        for offer in self:
            if offer.date_deadline:
                offer.validity = (
                    offer.date_deadline
                    - (
                        offer.create_date.date()
                        if offer.create_date
                        else fields.Date.today()
                    )
                ).days
            else:
                offer.validity = 7

    # Actions
    def action_accept_offer(self):
        for offer in self:
            offer.status = "accepted"
            offer.property_id.state = "offer_accepted"
            offer.property_id.buyer_id = offer.partner_id
            offer.property_id.selling_price = offer.price

    def action_refuse_offer(self):
        for offer in self:
            offer.status = "refused"
            offer.status = "refused"

    # Constraints
    _sql_constraints = [
        (
            "check_price_strictly_positive",
            "CHECK(price > 0)",
            "The offer price must be strictly positive.",
        )
    ]
