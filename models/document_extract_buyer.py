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


class DocumentExtractBuyer(models.Model):
    _name = "ntbies.document.extract.buyer"
    _description = "Extracted Buyer"
    _inherit = "ntbies.document.extract.contact.abstract"

    vat_number = fields.Char()
