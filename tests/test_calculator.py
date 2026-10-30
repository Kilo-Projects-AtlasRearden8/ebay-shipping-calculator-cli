"""Tests for the shipping math logic."""

import unittest

from ebay_shipping_calculator.calculator import (
    TIER_FIRST_CLASS,
    TIER_GROUND_ADVANTAGE,
    TIER_PRIORITY_MAIL,
    TIER_PRIORITY_MAIL_EXPRESS,
    billable_weight_oz,
    dimensional_weight_oz,
    estimate_shipping,
    format_money,
    shipping_margin_hint,
)


class DimensionalWeightTests(unittest.TestCase):
    def test_standard_divisor(self):
        # 12x12x12 = 1728 in^3; /166 * 16 = 166.55... oz
        self.assertAlmostEqual(dimensional_weight_oz(12, 12, 12), 166.55, places=1)

    def test_small_package(self):
        self.assertAlmostEqual(dimensional_weight_oz(6, 4, 2), 4.63, places=1)


class BillableWeightTests(unittest.TestCase):
    def test_actual_wins_when_heavier(self):
        self.assertEqual(billable_weight_oz(100, (6, 4, 2)), 100)

    def test_dimensional_wins_when_larger(self):
        self.assertEqual(
            billable_weight_oz(5, (12, 12, 12)), dimensional_weight_oz(12, 12, 12)
        )

    def test_no_dims_returns_actual(self):
        self.assertEqual(billable_weight_oz(10), 10)


class EstimateTests(unittest.TestCase):
    def test_first_class_applicable_under_limit(self):
        result = estimate_shipping(10, TIER_FIRST_CLASS)
        self.assertTrue(result["applicable"])
        self.assertEqual(result["estimated_cost_usd"], 6.10)

    def test_first_class_not_applicable_over_limit(self):
        result = estimate_shipping(16, TIER_FIRST_CLASS)
        self.assertFalse(result["applicable"])
        self.assertIsNone(result["estimated_cost_usd"])

    def test_priority_mail_bracket(self):
        result = estimate_shipping(20, TIER_PRIORITY_MAIL)
        self.assertTrue(result["applicable"])
        self.assertEqual(result["estimated_cost_usd"], 12.05)

    def test_dimensional_weight_bumps_cost(self):
        light = estimate_shipping(5, TIER_PRIORITY_MAIL)
        big = estimate_shipping(5, TIER_PRIORITY_MAIL, dims=(20, 20, 20))
        self.assertGreater(big["billable_weight_oz"], light["billable_weight_oz"])
        self.assertTrue(big["note"])

    def test_all_tiers_have_labels(self):
        for tier in (
            TIER_FIRST_CLASS,
            TIER_GROUND_ADVANTAGE,
            TIER_PRIORITY_MAIL,
            TIER_PRIORITY_MAIL_EXPRESS,
        ):
            result = estimate_shipping(10, tier)
            self.assertTrue(result["tier_label"])


class MarginHintTests(unittest.TestCase):
    def test_absorbing_shipping(self):
        hint = shipping_margin_hint(7.10, shipping_charged_usd=5.00)
        self.assertLess(hint.shipping_margin_usd, 0)
        self.assertIn("absorb", hint.hint)

    def test_covering_shipping(self):
        hint = shipping_margin_hint(7.10, shipping_charged_usd=8.00)
        self.assertEqual(hint.shipping_margin_usd, 0.90)

    def test_no_charge_gives_guidance(self):
        hint = shipping_margin_hint(7.10)
        self.assertIsNone(hint.shipping_margin_usd)
        self.assertIn("7.10", hint.hint)

    def test_percent_of_item(self):
        hint = shipping_margin_hint(
            7.10, shipping_charged_usd=8.00, item_price_usd=20.00
        )
        self.assertEqual(hint.shipping_as_percent_of_item, 35.5)
        self.assertIn("big share", hint.hint)


class FormattingTests(unittest.TestCase):
    def test_format_money(self):
        self.assertEqual(format_money(7.1), "$7.10")
        self.assertEqual(format_money(None), "n/a")


if __name__ == "__main__":
    unittest.main()
