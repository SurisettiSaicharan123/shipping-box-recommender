import json

from django.test import TestCase
from django.urls import reverse


class RecommendBoxApiTests(TestCase):
    """Uses fixtures/sample_data.json.

    Products: 1 Book(20x13x3, .3kg)  2 Mug(10^3, .4kg)  3 Laptop Sleeve(38x28x3, .6kg)
              4 Desk Lamp(45x20x15, 1.8kg)  5 Dumbbell Set(30x20x15, 12kg)  6 Banner(200x10x10)
    Boxes:    Small 0.80 (2kg)  Medium 1.50 (10kg)  Large 2.75 (20kg)  Heavy-Duty 3.60 (30kg)
    """

    fixtures = ["sample_data"]

    def post(self, body, raw=False):
        data = body if raw else json.dumps(body)
        return self.client.post(reverse("recommend-box"), data=data, content_type="application/json")

    def order(self, *pairs):
        return {"items": [{"product_id": p, "quantity": q} for p, q in pairs]}

    # ---- success cases ----
    def test_single_book_goes_in_small_box(self):
        res = self.post(self.order((1, 1)))
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["recommended_box"]["name"], "Small")
        self.assertEqual(body["recommended_box"]["cost"], "0.80")
        self.assertEqual(body["order_summary"]["total_units"], 1)
        self.assertEqual(len(body["placements"]), 1)

    def test_two_books_still_fit_small(self):
        self.assertEqual(self.post(self.order((1, 2))).json()["recommended_box"]["name"], "Small")

    def test_laptop_sleeve_needs_medium(self):
        self.assertEqual(self.post(self.order((3, 1))).json()["recommended_box"]["name"], "Medium")

    def test_six_mugs_need_medium(self):
        body = self.post(self.order((2, 6))).json()
        self.assertEqual(body["recommended_box"]["name"], "Medium")
        self.assertEqual(body["order_summary"]["total_units"], 6)
        self.assertAlmostEqual(body["order_summary"]["total_weight_kg"], 2.4)

    def test_long_lamp_needs_large(self):
        self.assertEqual(self.post(self.order((4, 1))).json()["recommended_box"]["name"], "Large")

    def test_heavy_item_picks_cheapest_box_with_capacity(self):
        # 12 kg exceeds Medium (10 kg); Large (2.75) is cheaper than Heavy-Duty (3.60).
        self.assertEqual(self.post(self.order((5, 1))).json()["recommended_box"]["name"], "Large")

    def test_duplicate_lines_are_merged(self):
        body = self.post(self.order((2, 3), (2, 3))).json()
        self.assertEqual(body["order_summary"]["total_units"], 6)

    def test_mixed_order(self):
        body = self.post(self.order((1, 1), (2, 1))).json()
        self.assertEqual(body["recommended_box"]["name"], "Medium")  # 20x13x3 + 10^3 too tight for Small

    # ---- no box fits ----
    def test_item_too_big_for_any_box(self):
        res = self.post(self.order((6, 1)))
        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.json()["error"], "no_box_fits")
        self.assertIn("too large", res.json()["message"])

    def test_order_too_heavy_for_any_box(self):
        res = self.post(self.order((5, 4)))  # 48 kg
        self.assertEqual(res.status_code, 422)
        self.assertIn("weighs", res.json()["message"])

    def test_each_item_fits_but_not_together(self):
        res = self.post(self.order((5, 2)))  # 24 kg, 18000 cm3: exceeds every box
        self.assertEqual(res.status_code, 422)
        self.assertIn("no single box", res.json()["message"])

    # ---- validation ----
    def test_unknown_product(self):
        res = self.post(self.order((999, 1)))
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["error"], "unknown_product")

    def test_invalid_json(self):
        res = self.post("{not json", raw=True)
        self.assertEqual((res.status_code, res.json()["error"]), (400, "invalid_json"))

    def test_empty_body(self):
        self.assertEqual(self.post("", raw=True).status_code, 400)

    def test_body_not_an_object(self):
        self.assertEqual(self.post([1, 2]).json()["error"], "invalid_body")

    def test_empty_items(self):
        self.assertEqual(self.post({"items": []}).json()["error"], "invalid_items")

    def test_missing_items(self):
        self.assertEqual(self.post({}).json()["error"], "invalid_items")

    def test_zero_quantity(self):
        self.assertEqual(self.post(self.order((1, 0))).status_code, 400)

    def test_negative_quantity(self):
        self.assertEqual(self.post(self.order((1, -3))).status_code, 400)

    def test_fractional_quantity(self):
        self.assertEqual(self.post({"items": [{"product_id": 1, "quantity": 1.5}]}).status_code, 400)

    def test_boolean_quantity_rejected(self):
        self.assertEqual(self.post({"items": [{"product_id": 1, "quantity": True}]}).status_code, 400)

    def test_string_product_id(self):
        self.assertEqual(self.post({"items": [{"product_id": "1", "quantity": 1}]}).status_code, 400)

    def test_item_not_an_object(self):
        self.assertEqual(self.post({"items": [5]}).json()["error"], "invalid_item")

    def test_too_many_units(self):
        res = self.post(self.order((2, 501)))
        self.assertEqual(res.json()["error"], "too_many_units")

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(reverse("recommend-box")).status_code, 405)

    def test_no_boxes_configured(self):
        from boxes.models import Box

        Box.objects.all().delete()
        res = self.post(self.order((1, 1)))
        self.assertEqual(res.status_code, 422)
        self.assertIn("No boxes", res.json()["message"])
