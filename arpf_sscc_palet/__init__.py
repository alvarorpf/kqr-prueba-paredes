from . import models


def post_init_hook(env):
    """Create the SSCC sequence of the companies that already exist."""
    env["res.company"].with_context(active_test=False).search([])._ensure_sscc_sequence()
