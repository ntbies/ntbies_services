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
        [("bill", "Bill"), ("expense", "Expense")],
        tracking=True,
        default="bill",
        string="Document type",
        help="This field is important as it helps to decide which extraction model should be used",
    )

    vat_amount = fields.Float(digits=(8, 2))
    total_amount = fields.Float(digits=(8, 2))
    total_vat_excluded = fields.Float(digits=(8, 2))
    currency = fields.Char()
    document_date = fields.Date()
    due_date = fields.Date()
    extraction_date = fields.Datetime(tracking=True)
    pages = fields.Integer()

    can_extract = fields.Boolean(compute="_compute_extract_configuration")
    auto_extract = fields.Boolean(compute="_compute_extract_configuration")
    auto_create = fields.Boolean(default=True)

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

    company_id = fields.Many2one(
        comodel_name="res.company", compute="_compute_company_id"
    )

    document_reference = fields.Char()
    is_readonly = fields.Boolean(compute="_compyte_is_readonly")

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

    def run_extraction(self):
        """
        Run extraction process for each record, updating
        status and posting messages as needed.
        """
        for record in self:
            record.run_single_document_extraction()

    def run_single_document_extraction(self):
        """
        Run extraction process for a single document, updating
        status and posting messages as needed.
        """
        self.ensure_one()
        if self.status == ["processing", "extracted", "processed"]:
            return
        access_key = self.company_id.ntbies_access_key if self.company_id else False
        service_name = f"ntbies.service.extract.{self.document_type}"
        try:
            service_model = self.env[service_name]
            resp = service_model.create_document(self.attachment_id, access_key)
            if resp.get("message"):
                self.status = "error"
                self.message_post(body=resp.get("message"))
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
            if self.bill_id:
                self.bill_id.message_post(
                    body="Extraction Initialization failed with this error %s"
                    % str(error)
                )

    def check_extraction(self):
        """
        Performs the extraction process for each record.
        :return:
        """
        for record in self:
            record.check_extraction_status()

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
        if self.status == ["extracted", "processed"]:
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
            content = resp.get("extract", {})
            data = {
                "status": "extracted",
                "currency": content.get("currency", False),
                "total_amount": content.get("total_amount", False),
                "document_date": parser.isoparse(content.get("invoice_date")).date()
                if content.get("invoice_date")
                else False,
                "extraction_date": parser.isoparse(resp.get("updated_at")).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if resp.get("updated_at")
                else False,
                "document_reference": content.get("reference", False),
            }
            if self.document_type == "bill":
                data.update(
                    {
                        "total_vat_excluded": content.get("total", False),
                        "vat_amount": content.get("vat_amount", False),
                        "currency": content.get("currency", False),
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
                lines = []
                for line in content.get("lines", []):
                    lines.append((0, 0, line))
                if lines:
                    data["line_ids"] = lines
                if self.line_ids:
                    self.line_ids.unlink()
            if self.document_type == "expense":
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
            self.write(data)
            self.with_delay(
                priority=0,
                eta=3,
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
            if record.document_type == "bill":
                record.generate_bill()
            if record.document_type == "expense":
                record.generate_expense()

    def generate_expense(self):
        self.ensure_one()
        self.env["ntbies.service.extract.expense"].generate(self)

    def generate_bill(self):
        """
        Generates an invoice for the document based on the extracted content.
        """
        self.ensure_one()
        self.env["ntbies.service.extract.bill"].generate(self)

    @api.depends(
        "buyer_id",
        "buyer_id.company_name",
        "vendor_id",
        "vendor_id.company_name",
        "document_reference",
    )
    def _compute_display_name(self):
        for record in self:
            name = record.name
            if record.vendor_id and record.vendor_id.company_name:
                name = record.vendor_id.company_name
            elif record.buyer_id and record.buyer_id.company_name:
                name = record.buyer_id.company_name
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

    @api.depends("bill_id", "bill_id.state")
    def _compyte_is_readonly(self):
        for record in self:
            is_readonly = False
            if record.bill_id and record.bill_id.state != "draft":
                is_readonly = True
            record.is_readonly = is_readonly

    @api.depends("bill_id", "expense_id")
    def _compute_company_id(self):
        for record in self:
            company = False
            if record.bill_id:
                company = record.bill_id.company_id
            elif record.expense_id:
                company = record.expense_id.company_id
            record.company_id = company

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
