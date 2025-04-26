import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def pre_init(env):

    expenses_categories = env["ir.model.data"].search(
        [
            ("module", "in", ("hr_expense", "ntbies_services")),
            ("model", "=", "product.product"),
            ("noupdate", "=", True),
        ]
    )
    expenses_categories.write({"noupdate": False})
