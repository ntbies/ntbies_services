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

{
    "name": "NTBIES Services",
    "version": "15.0.1.0.0",
    "summary": "Comprehensive Integration of NTBIES Services",
    "author": "NTBIES SRL",
    "description": """
    NTBIES Services Integration module offers a unified platform for
    document importation, company information auto-completion,
    and other specialized services provided to NTBIES's customers.
    """,
    "category": "Productivity",
    "website": "https://www.ntbies.com",
    "license": "AGPL-3",
    "depends": ["base", "account", "queue_job", "hr_expense"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/document_import_wizard.xml",
        "views/config_settings_view.xml",
        "views/account_move_views.xml",
        "views/hr_expense_views.xml",
        "views/document_extract_view.xml",
        "views/menu_items.xml",
        "data/queue_job_channels.xml",
    ],
    "images": ["static/description/icon.png", "static/description/settings.png"],
    "installable": True,
    "application": True,
    "auto_install": False,
}
