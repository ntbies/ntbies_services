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


class NtbiesConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ntbies_access_key = fields.Char(
        string="NTBIES Access Key",
        related="company_id.ntbies_access_key",
        readonly=False,
    )
    enable_auto_extraction = fields.Boolean(
        string="Enable Document Auto Extraction",
        related="company_id.enable_auto_extraction",
        readonly=False,
    )
