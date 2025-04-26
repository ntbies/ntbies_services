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

from dateutil import parser
from odoo import api, fields, models


class DocumentExtraction(models.Model):
    _inherit = "ntbies.document.extract"

    document_type = fields.Selection(
        selection_add=[("bill", "Bill")],
    )

    vat_amount = fields.Float(digits=(8, 2))
    total_vat_excluded = fields.Float(digits=(8, 2))
    currency = fields.Char()
    due_date = fields.Date()
    vendor_id = fields.Many2one(
        comodel_name="ntbies.document.extract.vendor", tracking=True, string="Vendor"
    )
    vendor_name = fields.Char(related="vendor_id.company_name", readonly=False)
    vendor_line_1 = fields.Char(related="vendor_id.line_1", readonly=False)
    vendor_line_2 = fields.Char(related="vendor_id.line_2", readonly=False)
    vendor_city = fields.Char(related="vendor_id.city", readonly=False)
    vendor_state = fields.Char(related="vendor_id.state", readonly=False)
    vendor_country = fields.Char(
        related="vendor_id.country", readonly=False, string="Bill Country"
    )
    vendor_postal_code = fields.Char(related="vendor_id.postal_code", readonly=False)
    vendor_vat_number = fields.Char(related="vendor_id.vat_number", readonly=False)

    buyer_id = fields.Many2one(
        comodel_name="ntbies.document.extract.buyer", tracking=True, string="Buyer"
    )

    line_ids = fields.One2many(
        comodel_name="ntbies.document.extract.lines",
        inverse_name="document_id",
        string="Lines",
    )
    bill_id = fields.Many2one(
        comodel_name="account.move",
        tracking=True,
    )

    def get_company_id(self):
        self.ensure_one()
        if self.bill_id:
            return self.bill_id.company_id
        return super().get_company_id()

    def _generate(self):
        self.ensure_one()
        if self.document_type == "bill":
            return self.generate_bill()
        super()._generate()

    def generate_bill(self):
        """
        Generates an invoice for the document based on the extracted content.
        """
        self.ensure_one()
        self.env["ntbies.service.extract.bill"].generate(self)

    def get_extracted_data(self, response):
        data = super().get_extracted_data(response)
        if self.document_type == "bill":
            content = response.get("extract", {})
            data.update(
                {
                    "currency": content.get("currency", False),
                    "total_amount": content.get("total_amount", False),
                    "document_date": parser.isoparse(content.get("invoice_date")).date()
                    if content.get("invoice_date")
                    else False,
                    "total_vat_excluded": content.get("total", False),
                    "vat_amount": content.get("vat_amount", False),
                    "due_date": parser.isoparse(content.get("due_date")).date()
                    if content.get("due_date")
                    else False,
                }
            )
            if content.get("vendor") and any(content.get("vendor", {}).values()):
                if self.vendor_id:
                    self.vendor_id.write(content.get("vendor"))
                else:
                    vendor = self.env["ntbies.document.extract.vendor"].create(
                        content.get("vendor")
                    )
                    data["vendor_id"] = vendor.id
            if content.get("buyer") and any(content.get("buyer", {}).values()):
                if self.buyer_id:
                    self.buyer_id.write(content.get("buyer"))
                else:
                    buyer = self.env["ntbies.document.extract.buyer"].create(
                        content.get("buyer")
                    )
                    data["buyer_id"] = buyer.id
            if content.get("lines"):
                lines = [(5, 0, 0)]
                for line in content.get("lines", []):
                    lines.append((0, 0, line))
                if lines:
                    data["line_ids"] = lines

        return data

    def get_is_readonly(self):
        self.ensure_one()
        if self.bill_id and self.bill_id.state != "draft":
            return True
        return super().get_is_readonly()

    @api.model
    def extract_model_for_bill(self, bill):
        attachment = bill.message_main_attachment_id
        res = {
            "bill_id": bill.id,
            "document_type": "bill",
            "attachment_id": attachment.id,
            "name": attachment.name,
        }
        extract = self.create(res)
        bill.document_extract_id = extract
        return extract
