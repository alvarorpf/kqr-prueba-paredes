from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .utils import sscc

SSCC_SEQUENCE_CODE = "arpf.sscc.palet"


class ResCompany(models.Model):
    _inherit = "res.company"

    prefijo_gs1 = fields.Char(
        string="GS1 Company Prefix",
        copy=False,
        help="GS1 company prefix assigned to this company (6 to 12 digits). "
        "It is embedded in every SSCC generated for the company's pallets.",
    )

    _prefijo_gs1_uniq = models.Constraint(
        "UNIQUE(prefijo_gs1)",
        "Each company needs its own GS1 company prefix.",
    )

    @api.constrains("prefijo_gs1")
    def _check_prefijo_gs1(self):
        for company in self.filtered("prefijo_gs1"):
            if not sscc.is_valid_prefix(company.prefijo_gs1):
                raise ValidationError(
                    self.env._(
                        "The GS1 company prefix of %(company)s must contain only "
                        "digits and be between %(min)s and %(max)s digits long.",
                        company=company.display_name,
                        min=sscc.MIN_PREFIX_LENGTH,
                        max=sscc.MAX_PREFIX_LENGTH,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        companies._ensure_sscc_sequence()
        return companies

    def _ensure_sscc_sequence(self):
        """Return the SSCC sequences of ``self``, creating the missing ones.

        ``sudo`` is justified: the sequence is a technical record that warehouse
        users must not need access rights on just to create a package.
        """
        sequences = self.env["ir.sequence"].sudo()
        found = sequences.search(
            [("code", "=", SSCC_SEQUENCE_CODE), ("company_id", "in", self.ids)]
        )
        covered = set(found.company_id.ids)
        missing = self.filtered(lambda company: company.id not in covered)
        created = sequences.create(
            [
                {
                    "name": f"SSCC pallet - {company.name}",
                    "code": SSCC_SEQUENCE_CODE,
                    "company_id": company.id,
                    "implementation": "standard",  # PostgreSQL sequence: concurrency-safe
                    "padding": 0,
                    "number_next": 1,
                    "number_increment": 1,
                }
                for company in missing
            ]
        )
        return found | created
