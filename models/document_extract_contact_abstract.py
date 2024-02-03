# Odoo Module to Integrate NTBIES Services
# Streamlining data extraction from invoices, vendor bills, and prefilling business contact information.
# Copyright (C) 2024 Gerry Ntabuhashe for NTBIES SRL

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from odoo import models, fields


class DocumentExtractContactAbstract(models.AbstractModel):
    _name = "ntbies.document.extract.contact.abstract"
    _description = "Extracted Contact Abstract"
    _rec_name = "company_name"

    company_name = fields.Char()
    line_1 = fields.Char()
    line_2 = fields.Char()
    postal_code = fields.Char()
    city = fields.Char()
    country = fields.Char()
    state = fields.Char()
    partner_id = fields.Many2one("res.partner", ondelete="set null")

    def find_or_create_partner(self):
        """
        Find or create a partner based on the partner name
        :return:
        """
        self.ensure_one()
        partner_model = self.env["res.partner"]
        partner = partner_model.search(
            [
                ("name", "=", self.company_name),
            ],
            limit=1,
        )
        if partner:
            return partner
        return partner_model.create(self.prepare_partner_data())

    def prepare_partner_data(self):
        """
        Prepare partner data for creating a new partner
        :return:
        """
        return {
            "name": self.company_name,
            "street": self.line_1,
            "street2": self.line_2,
            "zip": self.postal_code,
            "city": self.city,
            "state_id": self.env["res.country.state"]
            .search(
                [
                    ("code", "=", self.state),
                ],
                limit=1,
            )
            .id
            if self.state
            else False,
            "country_id": self.env["res.country"]
            .search(
                [
                    ("code", "=", self.country),
                ],
                limit=1,
            )
            .id
            if self.country
            else False,
        }
