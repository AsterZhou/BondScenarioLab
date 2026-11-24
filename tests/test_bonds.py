import io
import unittest
from bond_scenarios import Bond, aggregate, read_positions

class PricingTests(unittest.TestCase):
    def setUp(self):
        self.bond = Bond("sample", "HKD", 100000, 4, 4, 10, 2)

    def test_par_at_coupon_yield(self):
        self.assertAlmostEqual(self.bond.price_duration()[0], 100)

    def test_zero_coupon_closed_form(self):
        bond = Bond("zero", "USD", 100, 0, 5, 8, 2)
        price, duration = bond.price_duration()
        self.assertAlmostEqual(price, 100 / 1.025**8)
        self.assertAlmostEqual(duration, 4 / 1.025)

    def test_central_dv01_matches_analytical_derivative(self):
        row = self.bond.scenario(0)
        approx = row["market_value"] * row["modified_duration_years"] * 0.0001
        self.assertAlmostEqual(row["dv01"], approx, places=4)
        self.assertEqual(row["scenario_pnl"], 0)

    def test_shocks_and_convexity(self):
        gain = self.bond.scenario(-100)["scenario_pnl"]
        loss = self.bond.scenario(100)["scenario_pnl"]
        self.assertLess(loss, 0)
        self.assertGreater(gain, -loss)

    def test_negative_yield(self):
        bond = Bond("neg", "USD", 100, 0, -1, 2, 1)
        self.assertGreater(bond.price_duration()[0], 100)
        with self.assertRaises(ValueError):
            bond.price_duration(-10000)

    def test_currency_and_shocks_stay_separate(self):
        other = Bond("usd", "USD", 25000, 0, 0, 1, 1)
        rows = [self.bond.scenario(100), self.bond.scenario(-100), other.scenario(100), self.bond.scenario(100)]
        groups = {(g["currency"], g["shock_bp"]): g for g in aggregate(rows)}
        self.assertEqual(len(groups), 3)
        self.assertAlmostEqual(groups["HKD", 100]["scenario_pnl"], 2*rows[0]["scenario_pnl"])

    def test_duplicate_ids_rejected(self):
        header = "bond_id,currency,face_held,coupon_pct,ytm_pct,periods_left,frequency\n"
        position = "DEMO,USD,1000,4,4,5,1\n"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            read_positions(io.StringIO(header + 2*position))

    def test_invalid_position(self):
        for args in [(float("nan"), 2), (0, 2), (1000, 3)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                Bond("sample", "HKD", args[0], 0, 4, 2, args[1])
