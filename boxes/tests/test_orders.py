import json

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from boxes.models import Box, Order, OrderItem, Product
from boxes.services.orders import recommend_for_order


class OrderFixtureMixin:
    """Uses fixtures/sample_data.json (see test_api.py for the product/box table)."""

    fixtures = ["sample_data"]

    def make_order(self, *pairs):
        order = Order.objects.create()
        for pid, qty in pairs:
            OrderItem.objects.create(order=order, product_id=pid, quantity=qty)
        return order


class OrderModelTests(OrderFixtureMixin, TestCase):
    def test_totals(self):
        order = self.make_order((1, 2), (2, 1))  # 2 books (0.3) + 1 mug (0.4)
        self.assertEqual(order.total_units, 3)
        self.assertAlmostEqual(order.total_weight, 1.0)

    def test_same_product_twice_in_one_order_rejected(self):
        order = self.make_order((1, 1))
        with self.assertRaises(IntegrityError), transaction.atomic():
            OrderItem.objects.create(order=order, product_id=1, quantity=1)

    def test_zero_quantity_rejected_by_database(self):
        order = Order.objects.create()
        with self.assertRaises(IntegrityError), transaction.atomic():
            OrderItem.objects.create(order=order, product_id=1, quantity=0)

    def test_products_in_orders_cannot_be_deleted(self):
        from django.db.models import ProtectedError

        self.make_order((1, 1))
        with self.assertRaises(ProtectedError):
            Product.objects.get(pk=1).delete()


class RecommendForOrderTests(OrderFixtureMixin, TestCase):
    def test_saves_cheapest_fitting_box(self):
        order = self.make_order((3, 1))  # laptop sleeve -> Medium
        result = recommend_for_order(order)
        order.refresh_from_db()
        self.assertEqual(result.box.name, "Medium")
        self.assertEqual(order.recommended_box.name, "Medium")
        self.assertIn("Medium", order.recommendation_message)

    def test_no_fit_clears_box_and_explains(self):
        order = self.make_order((6, 1))  # 200 cm banner
        self.assertIsNone(recommend_for_order(order))
        order.refresh_from_db()
        self.assertIsNone(order.recommended_box)
        self.assertIn("too large", order.recommendation_message)

    def test_recalculation_follows_changes(self):
        order = self.make_order((1, 1))
        recommend_for_order(order)
        self.assertEqual(order.recommended_box.name, "Small")
        OrderItem.objects.create(order=order, product_id=5, quantity=1)  # 12 kg dumbbells
        recommend_for_order(order)
        self.assertEqual(order.recommended_box.name, "Large")

    def test_stale_box_is_cleared_when_order_stops_fitting(self):
        order = self.make_order((1, 1))
        recommend_for_order(order)
        OrderItem.objects.create(order=order, product_id=6, quantity=1)
        recommend_for_order(order)
        self.assertIsNone(order.recommended_box)

    def test_empty_order(self):
        order = Order.objects.create()
        self.assertIsNone(recommend_for_order(order))
        self.assertEqual(order.recommendation_message, "Order has no items.")

    def test_deleting_box_keeps_order(self):
        order = self.make_order((1, 1))
        recommend_for_order(order)
        order.recommended_box.delete()
        order.refresh_from_db()
        self.assertIsNone(order.recommended_box)


class OrderAdminFlowTests(OrderFixtureMixin, TestCase):
    """The demo path: log into /admin/, add an order with items, see the box."""

    def setUp(self):
        user = get_user_model().objects.create_superuser("admin", "a@example.com", "pw")
        self.client.force_login(user)

    def add_order(self, *pairs):
        data = {
            "items-TOTAL_FORMS": str(len(pairs)),
            "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "1",
            "items-MAX_NUM_FORMS": "1000",
        }
        for i, (pid, qty) in enumerate(pairs):
            data[f"items-{i}-product"] = str(pid)
            data[f"items-{i}-quantity"] = str(qty)
        return self.client.post(reverse("admin:boxes_order_add"), data, follow=True)

    def test_add_page_loads(self):
        self.assertEqual(self.client.get(reverse("admin:boxes_order_add")).status_code, 200)

    def test_creating_order_computes_box(self):
        res = self.add_order((2, 6))  # six mugs
        self.assertEqual(res.status_code, 200)
        order = Order.objects.get()
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.recommended_box.name, "Medium")
        self.assertContains(res, "Medium")  # shown in the success message / list

    def test_order_with_no_fit_still_saved_with_warning(self):
        res = self.add_order((6, 1))
        order = Order.objects.get()
        self.assertIsNone(order.recommended_box)
        self.assertContains(res, "too large")

    def test_order_requires_at_least_one_item(self):
        res = self.add_order()
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(res.status_code, 200)  # form re-rendered with error

    def test_duplicate_product_shows_form_error_not_crash(self):
        res = self.add_order((1, 1), (1, 2))
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(res.status_code, 200)

    def test_recalculate_action(self):
        order = self.make_order((3, 1))
        res = self.client.post(
            reverse("admin:boxes_order_changelist"),
            {"action": "recalculate", "_selected_action": [order.pk]},
            follow=True,
        )
        order.refresh_from_db()
        self.assertEqual(order.recommended_box.name, "Medium")
        self.assertContains(res, "Medium")

    def test_change_page_shows_recommendation(self):
        order = self.make_order((3, 1))
        recommend_for_order(order)
        res = self.client.get(reverse("admin:boxes_order_change", args=[order.pk]))
        self.assertContains(res, "Medium")


class OrderApiTests(OrderFixtureMixin, TestCase):
    def post(self, body, raw=False):
        data = body if raw else json.dumps(body)
        return self.client.post(reverse("order-create"), data=data, content_type="application/json")

    def test_create_returns_order_and_box(self):
        res = self.post({"items": [{"product_id": 2, "quantity": 6}]})
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertEqual(body["recommended_box"]["name"], "Medium")
        self.assertEqual(body["total_units"], 6)
        self.assertEqual(body["items"][0]["product"], "Coffee Mug")
        self.assertEqual(Order.objects.count(), 1)

    def test_duplicate_lines_merged(self):
        res = self.post({"items": [{"product_id": 2, "quantity": 3}, {"product_id": 2, "quantity": 3}]})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(res.json()["total_units"], 6)

    def test_no_fit_still_creates_order(self):
        res = self.post({"items": [{"product_id": 6, "quantity": 1}]})
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertIsNone(body["recommended_box"])
        self.assertIn("too large", body["message"])

    def test_get_order_later(self):
        order_id = self.post({"items": [{"product_id": 3, "quantity": 1}]}).json()["order_id"]
        res = self.client.get(reverse("order-detail", args=[order_id]))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["recommended_box"]["name"], "Medium")

    def test_get_unknown_order(self):
        res = self.client.get(reverse("order-detail", args=[9999]))
        self.assertEqual((res.status_code, res.json()["error"]), (404, "not_found"))

    def test_unknown_product_creates_nothing(self):
        res = self.post({"items": [{"product_id": 999, "quantity": 1}]})
        self.assertEqual(res.status_code, 404)
        self.assertEqual(Order.objects.count(), 0)

    def test_invalid_input_creates_nothing(self):
        for body in ({}, {"items": []}, {"items": [{"product_id": 1, "quantity": 0}]}):
            self.assertEqual(self.post(body).status_code, 400)
        self.assertEqual(self.post("{oops", raw=True).status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_wrong_methods(self):
        self.assertEqual(self.client.get(reverse("order-create")).status_code, 405)
        self.assertEqual(self.client.post(reverse("order-detail", args=[1])).status_code, 405)
