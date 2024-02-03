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

from odoo import api, fields, models


class DocumentExtractVendor(models.Model):
    _name = "ntbies.document.extract.lines"
    _description = "Extracted Bills Lines"
    _rec_name = "description"

    description = fields.Char(required=True)
    price = fields.Float(digits=(8, 2))
    quantity = fields.Float()
    tax = fields.Float(digits=(8, 2))
    amount = fields.Float(digits=(8, 2))
    document_id = fields.Many2one("ntbies.document.extract", ondelete="cascade")

    def get_as_line(self):
        product = self.find_or_create_product()
        return {
            "product_id": product.id,
            "quantity": self.quantity,
            "price_unit": self.price,
            "tax_ids": [(6, 0, [self.find_purchase_tax_by_percentage(self.tax).id])],
        }

    def find_or_create_product(self):
        product_model = self.env["product.product"]
        product = product_model.search(
            [
                ("name", "=", self.description),
            ],
            limit=1,
        )
        if not product:
            product_vals = {
                "name": self.description,
                "type": "service",
                "list_price": self.price,
                "purchase_ok": True,
            }
            product = product_model.create(product_vals)
        return product

    @api.model
    def find_purchase_tax_by_percentage(self, tax_percentage):
        domain = [("amount", "=", tax_percentage), ("type_tax_use", "=", "purchase")]
        return self.env["account.tax"].search(domain, limit=1)
