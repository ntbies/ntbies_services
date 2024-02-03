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


class DocumentExtractExpense(models.Model):
    _name = "ntbies.document.extract.expense"
    _description = "Extracted Expense"
    _rec_name = "description"

    description = fields.Char()
    category = fields.Char()
    country = fields.Char()

    def get_category(self):
        self.ensure_one()
        if self.category:
            product = self.env["product.product"].search(
                [("can_be_expensed", "=", True), ("name", "ilike", self.category)],
                limit=1,
            )
            return product
        return False
