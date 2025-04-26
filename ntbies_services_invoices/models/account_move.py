from odoo import _, api, fields, models
from odoo.addons.queue_job.job import identity_exact
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    document_extract_id = fields.Many2one(
        "ntbies.document.extract",
        string="Extraction document",
        ondelete="set null",
        copy=False,
    )

    def ntbies_extract_document(self):
        extract_model = self.env["ntbies.document.extract"]

        for record in self:
            if (
                not record.document_extract_id
                and record.move_type in ["in_invoice"]
                and record.state == "draft"
                and record.message_main_attachment_id
            ):
                extract = extract_model.extract_model_for_bill(record)
                if extract:
                    extract.with_delay(
                        priority=0,
                        description="Launch Extraction  %s" % extract.name,
                        identity_key=identity_exact,
                    ).run_extraction()

    @api.model_create_multi
    def create(self, vals):
        account_moves = super(AccountMove, self).create(vals)
        for rec in account_moves:
            if rec.company_id and rec.company_id.enable_auto_extraction:
                rec.with_delay(
                    priority=0,
                    eta=2,
                    description="Automatically Schedule document extraction",
                    identity_key=identity_exact,
                ).ntbies_extract_document()
        return account_moves

    def ntbies_open_extraction(self):
        self.ensure_one()
        if not self.document_extract_id:
            raise UserError(_("There is not any extraction performed for this bill"))
        return {
            "type": "ir.actions.act_window",
            "res_model": "ntbies.document.extract",
            "views": [[False, "form"]],
            "res_id": self.document_extract_id.id,
            "target": "self",
        }
