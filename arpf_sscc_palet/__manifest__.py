{
    "name": "SSCC for Pallets",
    "version": "19.0.1.0.0",
    "category": "Inventory/Inventory",
    "summary": "Unique GS1 SSCC-18 for every stock package, one sequence per company",
    "description": """
Assigns every ``stock.package`` a valid and unique SSCC (GS1-128 logistic label
base): extension digit + GS1 company prefix + serial reference + mod-10 check digit.
The GS1 company prefix is configured on each company and each company draws its
serial references from its own sequence.
    """,
    "author": "Alvaro Paredes",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": [
        "views/res_company_views.xml",
        "views/stock_package_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
