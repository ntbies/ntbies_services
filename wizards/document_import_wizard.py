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

from odoo import models, fields, _
from odoo.exceptions import UserError


class DocumentImportWizard(models.TransientModel):
    _name = "ntbies.document.import.wizard"
    _description = "Import Documents for Extraction"

    document_type = fields.Selection(
        [
            ("bill", "Bill"),
        ],
        required=True,
        default="bill",
        string="Document type",
        help="This field is important as it helps to know which model to use for document processing",
    )

    attachment_ids = fields.Many2many("ir.attachment", string="Files")

    def action_import_document(self):
        errors = []
        for attachment in self.attachment_ids:
            if attachment.mimetype not in [
                "application/pdf",
                "image/png",
                "image/jpeg",
                "image/tiff",
                "image/bmp",
            ]:
                errors.append("File {}".format(attachment.name))
            obj = self.env["ntbies.document.extract"].create(
                {
                    "name": attachment.name or _("New Document"),
                    "attachment_id": attachment.id,
                    "document_type": self.document_type,
                    "status": "new",
                }
            )
            attachment.res_model = "ntbies.document.extract"
            attachment.res_id = obj.id
            attachment.register_as_main_attachment()
        if errors:
            raise UserError(
                _(
                    "Only PDF, PNG, JPG/JPEG, TIFF and BMP images are allowed.\n"
                    "All the following documents do not meet these requirements:\n- {}"
                ).format("\n- ".join(errors))
            )
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }
