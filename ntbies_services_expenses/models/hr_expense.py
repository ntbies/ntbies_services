from odoo import _, api, fields, models
from odoo.addons.queue_job.job import identity_exact
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = "hr.expense"

    document_extract_id = fields.Many2one(
        "ntbies.document.extract",
        string="Extraction document",
        ondelete="set null",
        copy=False,
    )

    def ntbies_extract_document(self):
        extract_model = self.env["ntbies.document.extract"]
        for expense in self:
            if expense.state != "draft" or expense.sheet_id:
                raise UserError(
                    "You can't perform extraction of an expense not in draft"
                )

        for expense in self:
            if not expense.document_extract_id and expense.message_main_attachment_id:
                extract = extract_model.extract_model_for_expense(expense)
                if extract:
                    extract.with_delay(
                        priority=0,
                        description="Launch Extraction  %s" % extract.name,
                        identity_key=identity_exact,
                    ).run_extraction()

    @api.model_create_multi
    def create(self, vals):
        expenses = super(HrExpense, self).create(vals)
        for rec in expenses:
            if rec.company_id and rec.company_id.enable_auto_extraction:
                rec.with_delay(
                    priority=0,
                    eta=2,
                    description="Automatically Schedule document extraction",
                    identity_key=identity_exact,
                ).ntbies_extract_document()
        return expenses

    def ntbies_open_extraction(self):
        self.ensure_one()
        if not self.document_extract_id:
            raise UserError(_("There is no extraction performed for this expense"))
        return {
            "type": "ir.actions.act_window",
            "res_model": "ntbies.document.extract",
            "views": [[False, "form"]],
            "res_id": self.document_extract_id.id,
            "target": "self",
        }
