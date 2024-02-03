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

from odoo import api, models


class ServiceExtractExpense(models.AbstractModel):
    _name = "ntbies.service.extract.expense"
    _description = "Ntbies Service Extract Expense"
    _inherit = "ntbies.service.extract"

    def create_document(self, attachment, access_key):
        """
        Creates a document using the provided attachment and access key.

        :param attachment: The attachment object containing the raw file content and name.
        :param access_key: The access key for authentication.
        :return: The response from the post request, which includes the created document information.
        """
        file_content = attachment.raw
        file_name = attachment.name
        files = {"document": (file_name, file_content)}
        return self.post_request(
            "documents", access_key, files=files, payload={"type": "expense"}
        )

    def generate(self, document):
        document.ensure_one()
        currency_id = document.get_currency_and_activate_if_inactive()
        expense_vals = {
            "description": document.exp_description,
            "date": document.document_date,
            "currency_id": currency_id.id,
            "total_amount": document.total_amount,
        }
        if document.extracted_expense_id:
            expense_vals["product_id"] = document.extracted_expense_id.get_category()
        if document.expense_id:
            document.expense_id.write(expense_vals)
        document.status = "processed"
        document.message_post(body="Document processed successfully")

    @api.model
    def get_expense_category(self, category):
        if not category:
            return False
