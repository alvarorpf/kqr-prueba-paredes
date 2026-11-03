# arpf_sscc_palet — SSCC for pallets (Odoo 19)

Assigns every `stock.package` a valid, unique, read-only SSCC-18.

```
SSCC = extension digit (0) + GS1 company prefix + serial reference + mod-10 check digit
        1 digit            6-12 digits           pads to 17 digits    1 digit
```

| Company   | Prefix      | Serial digits | First SSCC                      |
|-----------|-------------|---------------|---------------------------------|
| Company A | `8412345`   | 9             | `0` `8412345` `000000001` + `d` |
| Company B | `841234567` | 7             | `0` `841234567` `0000001` + `d` |

Check against the public GS1 example: `10614141123456789` -> check digit `7`
-> `106141411234567897` (see `tests/test_sscc_palet.py`).

## Initial setup (required, once per company)

1. Install `arpf_sscc_palet`. A serial sequence is created automatically for
   every existing company (`post_init_hook`) and for each company created later.
2. *Inventory > Configuration > Settings > Operations*: enable **Packages**
   (Odoo requirement, needed to see the Packages menu).
3. For **each company**: *Settings > Users & Companies > Companies > (company)*,
   fill **GS1 Company Prefix** (digits only, 6 to 12, unique per company).
4. Create packages. Each company must be the active one when it creates them.

Without step 3 the creation is blocked on purpose:

> Invalid Operation - Company My Company has no GS1 company prefix. Set it in the
> company form before creating packages.

The failed attempt does not consume a serial number (the check runs before the
sequence is read).

## Design decisions

- **Company comes from the environment, not from the package.** In Odoo 19
  `stock.package.company_id` is *computed from its content* (`readonly`, stored),
  so a new empty package has no company. The SSCC uses `env.company` (or an
  explicit `company_id` in `vals`).
- **One `ir.sequence` per company** (`implementation="standard"` = PostgreSQL
  sequence, safe under concurrency). Created when a company is created and, for
  existing ones, in `post_init_hook`. Serial padding is done in Python because it
  depends on the prefix length. Sequence access uses `sudo` on purpose, so
  warehouse users need no rights on `ir.sequence`.
- **Uniqueness = global `UNIQUE(sscc)`**, not per company. Prefix A (`8412345`) is
  a *prefix of* prefix B (`841234567`), so A with serial `670000001` produces the
  same 17 digits as B with serial `0000001`. GS1 normally allocates prefix-free
  ranges; with this data only the database constraint can guarantee uniqueness
  (covered by `test_database_rejects_colliding_sscc_between_companies`).
  Reaching that range needs ~670 M pallets in company A; the insert then fails
  with an integrity error instead of producing a duplicate.
- **Read-only at ORM level**, not only in the view: `write` rejects `sscc`,
  `create` ignores a supplied value, `copy=False`.
- **Company without prefix -> `UserError` on package creation.** Fail loud rather
  than creating packages without a label code. Installing the module therefore
  requires configuring the prefix on every company that creates packages.
- **No `size` on `prefijo_gs1`**: Odoo silently truncates `Char(size=n)`; length
  is validated by a constraint instead. Prefix is also `UNIQUE` per company.
- Odoo 19 idioms: `models.Constraint`, `self.env._()`, `group_ids` on users.

## Known limits / out of scope

- Packages created before installing the module keep `sscc = NULL`
  (the migration script is out of scope).
- Changing a company prefix does not touch existing SSCCs; the serial keeps counting.
- Serial overflow (9 digits for A, 7 for B) raises a `UserError`.

## Run the tests

```bash
odoo-bin -d <db> -i arpf_sscc_palet --test-tags /arpf_sscc_palet --stop-after-init
```

PostgreSQL sequences are not rolled back between tests; the tests restart them in
`setUp` (`ALTER SEQUENCE` *is* transactional).

## Manual validation in the browser (Odoo 19.0, fresh DB, no demo data)

Full flow from a clean database, in the order of "Initial setup" above.

Run with Playwright against a local server; both companies configured from the UI.

| Step | Result |
|------|--------|
| New package before configuring any prefix | `Invalid Operation`, nothing saved |
| Company form shows **GS1 Company Prefix** | OK |
| Save prefix `abc12` | `Validation Error`: digits only, 6 to 12 long |
| Company A (`8412345`) -> new package | SSCC `084123450000000010` |
| Company B (`841234567`) -> new package | SSCC `084123456700000015` |
| SSCC field in the package form | rendered read-only |
| DB | 2 packages (18 digits), 1 `arpf.sscc.palet` sequence per company |
| Server log / browser console | no errors (only the expected validation warning) |

Check digits recomputed by hand (weights 3,1,3,... from the right): sums 50 and 75
-> digits 0 and 5.
