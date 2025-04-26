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
        selection_add=[("expense", "Expense")],
    )

    extracted_expense_id = fields.Many2one(
        comodel_name="ntbies.document.extract.expense",
        ondelete="set null",
    )
    exp_description = fields.Char(related="extracted_expense_id.description")
    exp_category = fields.Char(related="extracted_expense_id.category")
    exp_country = fields.Char(related="extracted_expense_id.country")

    expense_id = fields.Many2one(
        comodel_name="hr.expense",
        tracking=True,
    )

    def _generate(self):
        self.ensure_one()
        if self.document_type == "expense":
            return self.generate_expense()
        super()._generate()

    def generate_expense(self):
        self.ensure_one()
        self.env["ntbies.service.extract.expense"].generate(self)

    def get_extracted_data(self, response):
        data = super().get_extracted_data(response)
        if self.document_type == "expense":
            content = response.get("extract", {})
            data.update(
                {
                    "currency": content.get("currency", False),
                    "total_amount": content.get("total_amount", False),
                    "document_date": parser.isoparse(content.get("invoice_date")).date()
                    if content.get("invoice_date")
                    else False,
                }
            )
            if self.extracted_expense_id:
                self.extracted_expense_id.unlink()
            extracted_expense = self.env["ntbies.document.extract.expense"].create(
                {
                    "description": content.get("description", False),
                    "category": content.get("category", False),
                    "country": content.get("country", False),
                }
            )
            data["extracted_expense_id"] = extracted_expense.id
        return data

    def get_company_id(self):
        self.ensure_one()
        if self.expense_id:
            return self.expense_id.company_id
        return super().get_company_id()

    def extract_model_for_expense(self, expense):
        attachment = expense.message_main_attachment_id
        res = {
            "expense_id": expense.id,
            "document_type": "expense",
            "attachment_id": attachment.id,
            "name": attachment.name,
        }
        extract = self.create(res)
        expense.document_extract_id = extract
        return extract
