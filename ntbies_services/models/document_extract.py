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
from odoo.addons.queue_job.job import identity_exact
from odoo.exceptions import UserError


class DocumentExtraction(models.Model):
    _name = "ntbies.document.extract"
    _description = "Document"
    _inherit = ["mail.thread.main.attachment", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char("Name", required=True)

    attachment_id = fields.Many2one("ir.attachment", string="Attachment")

    status = fields.Selection(
        [
            ("new", "New"),
            ("processing", "Processing"),
            ("extracted", "Extracted"),
            ("processed", "Processed"),
            ("error", "Error"),
        ],
        default="new",
        tracking=True,
        string="Status",
    )

    reference = fields.Char(help="Document reference on Service platform")

    document_type = fields.Selection(
        [],
        tracking=True,
        string="Document type",
        help="This field is important as it helps to decide which extraction model should be used",
    )
    total_amount = fields.Float(digits=(8, 2))
    currency = fields.Char()
    document_date = fields.Date()
    extraction_date = fields.Datetime(tracking=True)
    pages = fields.Integer()

    can_extract = fields.Boolean(compute="_compute_extract_configuration")
    auto_extract = fields.Boolean(compute="_compute_extract_configuration")
    auto_create = fields.Boolean(default=True)

    company_id = fields.Many2one(
        comodel_name="res.company", compute="_compute_company_id"
    )
    document_reference = fields.Char()
    is_readonly = fields.Boolean(compute="_compute_is_readonly")

    # vat_amount = fields.Float(digits=(8, 2))
    # total_vat_excluded = fields.Float(digits=(8, 2))
    # currency = fields.Char()
    # due_date = fields.Date()
    # vendor_id = fields.Many2one(
    #     comodel_name="ntbies.document.extract.vendor", tracking=True, string="Vendor"
    # )
    # vendor_name = fields.Char(related="vendor_id.company_name", readonly=False)
    # vendor_line_1 = fields.Char(related="vendor_id.line_1", readonly=False)
    # vendor_line_2 = fields.Char(related="vendor_id.line_2", readonly=False)
    # vendor_city = fields.Char(related="vendor_id.city", readonly=False)
    # vendor_state = fields.Char(related="vendor_id.state", readonly=False)
    # vendor_country = fields.Char(
    #     related="vendor_id.country", readonly=False, string="Bill Country"
    # )
    # vendor_postal_code = fields.Char(related="vendor_id.postal_code", readonly=False)
    # vendor_vat_number = fields.Char(related="vendor_id.vat_number", readonly=False)
    #
    # buyer_id = fields.Many2one(
    #     comodel_name="ntbies.document.extract.buyer", tracking=True, string="Buyer"
    # )
    #
    # line_ids = fields.One2many(
    #     comodel_name="ntbies.document.extract.lines",
    #     inverse_name="document_id",
    #     string="Lines",
    # )
    # bill_id = fields.Many2one(
    #     comodel_name="account.move",
    #     tracking=True,
    # )
    #

    def run_extraction(self):
        """
        Run extraction process for each record, updating
        status and posting messages as needed.
        """
        for record in self:
            record.run_single_document_extraction()

    def can_extract_document(self):
        return self.document_type and self.status not in [
            "processing",
            "extracted",
            "processed",
        ]

    def run_single_document_extraction(self):
        """
        Run extraction process for a single document, updating
        status and posting messages as needed.
        """
        self.ensure_one()
        if not self.can_extract_document():
            return False
        access_key = self.company_id.ntbies_access_key if self.company_id else False
        service_name = f"ntbies.service.extract.{self.document_type}"
        try:
            service_model = self.env[service_name]
            resp = service_model.create_document(self.attachment_id, access_key)
            if resp.get("message"):
                self.status = "error"
                self.message_post(body=resp.get("message"))
                return False
            else:
                self.status = "processing"
                self.update(
                    {
                        "pages": resp.get("pages"),
                        "reference": resp.get("id"),
                    }
                )
                self.message_post(
                    body="Extraction started and will cost the equivalent of {} pages".format(
                        resp.get("pages")
                    )
                )
                self.with_delay(
                    priority=0,
                    eta=20,
                    channel="document_extraction",
                    description="Check Extraction status  %s" % self.reference,
                    identity_key=identity_exact,
                ).check_extraction()
                return True
        except KeyError:
            self.status = "error"
            self.message_post(
                body="The extraction of this document type is not yet supported"
            )
        except Exception as error:
            self.status = "error"
            self.message_post(
                body="We've encountered the following error %s" % str(error)
            )
        return False

    def check_extraction(self):
        """
        Performs the extraction process for each record.
        :return:
        """
        for record in self:
            record.check_extraction_status()

    def get_extracted_data(self, response):
        content = response.get("extract", {})
        return {
            "status": "extracted",
            "extraction_date": parser.isoparse(response.get("updated_at")).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            if response.get("updated_at")
            else False,
            "document_reference": content.get("reference", False),
        }

    def check_extraction_status(self):
        """
        Performs the extraction process for each record.
        It retrieves the access key from the company environment
        and then iterates through each record.
        It calls a service to get document information and updates
        the status and posts messages based on the response.
        It also processes the extracted content and updates the record accordingly.
        If an error occurs, it handles the error and posts a message.
        """
        self.ensure_one()
        if not self.document_type or self.status in ["extracted", "processed"]:
            return
        access_key = self.company_id.ntbies_access_key if self.company_id else False
        if not self.reference:
            self.message_post(body="Document unknown by the service")
            return
        service_name = f"ntbies.service.extract.{self.document_type}"
        try:
            service_model = self.env[service_name]
            resp = service_model.get_document_info(access_key, self.reference)
            if resp.get("status") in ["error"]:
                self.status = "error"
                return
            if resp.get("message"):
                raise UserError(resp.get("message"))

            data = self.get_extracted_data(resp)
            self.write(data)
            self.with_delay(
                priority=0,
                eta=1,
                channel="document_extraction",
                description="Check Extraction status  %s" % self.reference,
                identity_key=identity_exact,
            ).dispatch()
        except KeyError:
            self.status = "error"
            self.message_post(
                body="The extraction of this document type is not yet supported"
            )

    def dispatch(self):
        """
        Generates an accounting record for the document based on the extracted content.
        """
        for record in self:
            if record.status != "extracted":
                raise UserError("Document not processed yet")
            record._generate()

    def _generate(self):
        self.ensure_one()
        # if self.document_type == "bill":
        #     self.generate_bill()
        # if self.document_type == "expense":
        #     self.generate_expense()

    @api.depends("document_reference")
    def _compute_display_name(self):
        for record in self:
            name = record.name
            if record.document_reference:
                name = "{0} ({1})".format(name, self.document_reference)
            record.display_name = name

    def unlink(self):
        """
        Unlinks the current record related attachment, then calls the parent class's unlink method.
        """
        for record in self:
            if record.attachment_id:
                record.attachment_id.unlink()
        return super().unlink()

    def _compute_extract_configuration(self):
        access_key = self.company_id.ntbies_access_key if self.company_id else False
        auto_extract = self.env.company.enable_auto_extraction
        for record in self:
            record.auto_extract = auto_extract
            if not access_key:
                record.can_extract = False
            else:
                record.can_extract = True

    def _compute_is_readonly(self):
        print("Is readonly calculated")
        for record in self:
            record.is_readonly = record.get_is_readonly()

    def get_is_readonly(self):
        self.ensure_one()
        # is_readonly = False
        # if self.bill_id and self.bill_id.state != "draft":
        #     is_readonly = True
        return False

    # @api.depends("bill_id", "expense_id")
    def _compute_company_id(self):
        for record in self:
            record.company_id = record.get_company_id()

    def get_company_id(self):
        self.ensure_one()
        return False

    def placeholder_button(self):
        """
        This method is just a placeholder fot the button
        """
        pass

    def get_currency_and_activate_if_inactive(self):
        currency = (
            self.env["res.currency"]
            .with_context(active_test=False)
            .search([("name", "ilike", self.currency or "EUR")], limit=1)
        )
        if currency and not currency.active:
            currency.active = True
        return currency

    # @api.model
    # def extract_model_for_bill(self, bill):
    #     attachment = bill.message_main_attachment_id
    #     res = {
    #         "bill_id": bill.id,
    #         "document_type": "bill",
    #         "attachment_id": attachment.id,
    #         "name": attachment.name,
    #     }
    #     extract = self.create([res])
    #     bill.document_extract_id = extract
    #     return extract
    #
    # @api.model
    # def extract_model_for_expense(self, expense):
    #     attachment = expense.message_main_attachment_id
    #     res = {
    #         "expense_id": expense.id,
    #         "document_type": "expense",
    #         "attachment_id": attachment.id,
    #         "name": attachment.name,
    #     }
    #     extract = self.create([res])
    #     expense.document_extract_id = extract
    #     return extract
