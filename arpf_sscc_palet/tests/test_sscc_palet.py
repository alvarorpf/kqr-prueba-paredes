from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger
from odoo.tools.barcode import check_barcode_encoding

from ..models.utils import sscc

PREFIX_A = "8412345"  # 7 digits  -> 9 serial digits
PREFIX_B = "841234567"  # 9 digits  -> 7 serial digits


@tagged("post_install", "-at_install")
class TestSsccPalet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        companies = cls.env["res.company"].create(
            [
                {"name": "Company A", "prefijo_gs1": PREFIX_A},
                {"name": "Company B", "prefijo_gs1": PREFIX_B},
            ]
        )
        cls.company_a, cls.company_b = companies

    def setUp(self):
        super().setUp()
        # PostgreSQL sequences are not rolled back between tests (nextval is
        # non-transactional) but ALTER SEQUENCE is, so restart them per test.
        for company in (self.company_a, self.company_b):
            self._sequence(company).write({"number_next_actual": 1})

    def _new_package(self, company):
        return self.env["stock.package"].with_company(company).create({})

    def _sequence(self, company):
        return company._ensure_sscc_sequence()

    # -- GS1 algorithm ----------------------------------------------------

    def test_public_gs1_example_has_check_digit_7(self):
        self.assertEqual(sscc.compute_check_digit("10614141123456789"), 7)

    def test_public_gs1_example_builds_full_sscc(self):
        self.assertEqual(
            sscc.build_sscc("1", "0614141", 123456789), "106141411234567897"
        )

    # -- one test per company ---------------------------------------------

    def test_company_a_sscc_structure(self):
        code = self._new_package(self.company_a).sscc
        self.assertEqual(len(code), 18)
        self.assertEqual(code[0], "0")  # extension digit
        self.assertEqual(code[1:8], PREFIX_A)  # GS1 company prefix
        self.assertEqual(code[8:17], "000000001")  # 9-digit serial
        self.assertTrue(check_barcode_encoding(code, "sscc"))  # core mod-10 check

    def test_company_b_sscc_structure(self):
        code = self._new_package(self.company_b).sscc
        self.assertEqual(len(code), 18)
        self.assertEqual(code[0], "0")
        self.assertEqual(code[1:10], PREFIX_B)
        self.assertEqual(code[10:17], "0000001")  # 7-digit serial
        self.assertTrue(check_barcode_encoding(code, "sscc"))

    # -- sequences and uniqueness -------------------------------------------

    def test_each_company_has_its_own_sequence(self):
        a1, a2 = self.env["stock.package"].with_company(self.company_a).create([{}, {}])
        b1 = self._new_package(self.company_b)
        self.assertEqual([a1.sscc[8:17], a2.sscc[8:17]], ["000000001", "000000002"])
        self.assertEqual(b1.sscc[10:17], "0000001")

    def test_sscc_is_unique_across_many_packages(self):
        packages = self.env["stock.package"].with_company(self.company_a).create(
            [{} for _ in range(20)]
        ) | self.env["stock.package"].with_company(self.company_b).create(
            [{} for _ in range(20)]
        )
        self.assertEqual(len(set(packages.mapped("sscc"))), 40)

    def test_database_rejects_colliding_sscc_between_companies(self):
        """Prefix A is a prefix of prefix B: A serial 670000001 == B serial 0000001."""
        self._new_package(self.company_b)  # B serial 1
        self._sequence(self.company_a).write({"number_next_actual": 670000001})
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self._new_package(self.company_a)

    def test_copy_gets_a_new_sscc(self):
        original = self._new_package(self.company_a)
        self.assertNotEqual(original.copy().sscc, original.sscc)

    # -- read-only ----------------------------------------------------------

    def test_sscc_cannot_be_written(self):
        package = self._new_package(self.company_a)
        with self.assertRaises(UserError):
            package.write({"sscc": "0" * 18})

    def test_sscc_supplied_on_create_is_ignored(self):
        package = self.env["stock.package"].with_company(self.company_a).create(
            {"sscc": "9" * 18}
        )
        self.assertEqual(package.sscc[1:8], PREFIX_A)

    # -- configuration errors ---------------------------------------------

    def test_package_creation_fails_when_company_has_no_prefix(self):
        company = self.env["res.company"].create({"name": "No prefix"})
        with self.assertRaises(UserError):
            self._new_package(company)

    def test_serial_overflow_raises_user_error(self):
        self._sequence(self.company_b).write({"number_next_actual": 10**7})
        with self.assertRaises(UserError):
            self._new_package(self.company_b)

    def test_invalid_prefix_is_rejected(self):
        for bad_prefix in ("abc1234", "12345", "1234567890123", "84123 45"):
            with self.subTest(prefix=bad_prefix), self.assertRaises(ValidationError):
                self.company_a.prefijo_gs1 = bad_prefix

    def test_duplicated_prefix_is_rejected(self):
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.company_b.write({"prefijo_gs1": PREFIX_A})
            self.company_b.flush_recordset()

    # -- security ---------------------------------------------------------

    def test_warehouse_user_can_create_package_without_sequence_access(self):
        user = self.env["res.users"].create(
            {
                "name": "Warehouse user",
                "login": "arpf_sscc_wh_user",
                "company_id": self.company_a.id,
                "company_ids": [(6, 0, self.company_a.ids)],
                "group_ids": [(6, 0, [self.env.ref("stock.group_stock_user").id])],
            }
        )
        package = self.env["stock.package"].with_user(user).with_company(
            self.company_a
        ).create({})
        self.assertTrue(check_barcode_encoding(package.sscc, "sscc"))
