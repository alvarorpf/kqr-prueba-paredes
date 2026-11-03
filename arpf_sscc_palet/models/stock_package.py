from odoo import api, models, fields
from odoo.exceptions import UserError

from .utils import sscc


class StockPackage(models.Model):
    _inherit = "stock.package"

    sscc = fields.Char(
        string="SSCC",
        size=sscc.SSCC_LENGTH,
        readonly=True,
        copy=False,
        help="Serial Shipping Container Code (GS1), generated when the package is created.",
    )

    _sscc_uniq = models.Constraint(
        "UNIQUE(sscc)",
        "The SSCC must be unique.",
    )
    _sscc_format = models.Constraint(
        "CHECK(sscc IS NULL OR sscc ~ '^[0-9]{18}$')",
        "The SSCC must be made of exactly 18 digits.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        # ``company_id`` is computed from the content on stock.package, so an
        # empty new package has none: the company comes from the environment.
        vals_list = [
            dict(vals, sscc=self._generate_sscc(self._get_sscc_company(vals)))
            for vals in vals_list
        ]
        return super().create(vals_list)

    def write(self, vals):
        if "sscc" in vals:
            raise UserError(
                self.env._("The SSCC is generated automatically and cannot be modified.")
            )
        return super().write(vals)

    @api.model
    def _get_sscc_company(self, vals):
        if vals.get("company_id"):
            return self.env["res.company"].browse(vals["company_id"])
        return self.env.company

    @api.model
    def _generate_sscc(self, company):
        if not company.prefijo_gs1:
            raise UserError(
                self.env._(
                    "Company %(company)s has no GS1 company prefix. Set it in the "
                    "company form before creating packages.",
                    company=company.display_name,
                )
            )
        serial = int(company._ensure_sscc_sequence()._next())
        try:
            return sscc.build_sscc(sscc.EXTENSION_DIGIT, company.prefijo_gs1, serial)
        except ValueError as error:
            raise UserError(
                self.env._(
                    "Company %(company)s has run out of SSCC serial references: %(error)s",
                    company=company.display_name,
                    error=error,
                )
            ) from error
