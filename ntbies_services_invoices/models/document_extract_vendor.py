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

from odoo import fields, models


class DocumentExtractVendor(models.Model):
    _name = "ntbies.document.extract.vendor"
    _description = "Extracted Vendor"
    _inherit = "ntbies.document.extract.contact.abstract"

    vat_number = fields.Char()

    def find_or_create_partner(self):
        """
        Find or create a partner based on the VAT number
        :return: res.partner
        """
        partner_model = self.env["res.partner"]
        partner = False
        if self.vat_number:
            partner = partner_model.search(
                [
                    ("vat", "=", self.vat_number),
                ],
                limit=1,
            )
        if partner:
            return partner
        partner = super().find_or_create_partner()
        if partner and not partner.vat and self.vat_number:
            partner.is_company = True
            partner.vat = self.vat_number
        return partner

    def prepare_partner_data(self):
        """
        Prepare partner data for creating a new partner with a VAT number
        :return: dict
        """
        res = super().prepare_partner_data()
        res["vat"] = self.vat_number
        res["is_company"] = True
        return res
