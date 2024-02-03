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

from odoo import models


class ServiceExtractBill(models.AbstractModel):
    _name = "ntbies.service.extract.bill"
    _description = "Ntbies Service Extract Bill"
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
            "documents", access_key, files=files, payload={"type": "bill"}
        )

    def generate(self, document):
        """
        Generates a vendor bill for the document based on the extracted content.

        :param document: The document record.
        """
        document.ensure_one()
        invoice_line_ids = []
        for line in document.line_ids:
            invoice_line_ids.append((0, 0, line.get_as_line()))

        partner_id = document.vendor_id.find_or_create_partner()
        currency_id = document.get_currency_and_activate_if_inactive()
        invoice_vals = {
            "partner_id": partner_id.id,
            "move_type": "in_invoice",
            "invoice_line_ids": invoice_line_ids,
            "currency_id": currency_id.id,
            "invoice_date": document.document_date,
            "invoice_date_due": document.due_date,
            "date": document.document_date,
            "to_check": True,
            "ref": document.document_reference,
        }
        if not document.bill_id:
            bill = self.env["account.move"].create(invoice_vals)
            attachment = document.attachment_id.copy(
                {
                    "res_model": "account.move",
                    "res_id": bill.id,
                }
            )
            attachment.register_as_main_attachment()
            document.bill_id = bill
        else:
            document.bill_id.invoice_line_ids.unlink()
            document.bill_id.write(invoice_vals)

        document.status = "processed"
        document.message_post(body="Document processed successfully")
