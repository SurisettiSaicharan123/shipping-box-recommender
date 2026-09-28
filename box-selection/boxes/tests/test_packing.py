import random
from decimal import Decimal

from django.test import SimpleTestCase

from boxes.services.packing import (
    BoxSpec,
    InvalidInput,
    ItemSpec,
    explain_no_fit,
    fits_weight,
    item_fits_box_alone,
    pack_items,
    select_box,
)


def item(name="i", l=1, w=1, h=1, wt=1.0):
    return ItemSpec(name, l, w, h, wt)


def box(name="b", l=10, w=10, h=10, max_w=10.0, cost="1.00"):
    return BoxSpec(name, l, w, h, max_w, Decimal(cost))


def assert_valid_packing(testcase, placements, container, expected_count):
    """Every placement is inside the box and no two placements overlap."""
    testcase.assertEqual(len(placements), expected_count)
    for p in placements:
        testcase.assertGreaterEqual(p.x, -1e-9)
        testcase.assertGreaterEqual(p.y, -1e-9)
        testcase.assertGreaterEqual(p.z, -1e-9)
        testcase.assertLessEqual(p.x + p.length, container.length + 1e-6)
        testcase.assertLessEqual(p.y + p.width, container.width + 1e-6)
        testcase.assertLessEqual(p.z + p.height, container.height + 1e-6)
    for i, a in enumerate(placements):
        for b in placements[i + 1:]:
            overlap = (
                a.x < b.x + b.length - 1e-9 and b.x < a.x + a.length - 1e-9
                and a.y < b.y + b.width - 1e-9 and b.y < a.y + a.width - 1e-9
                and a.z < b.z + b.height - 1e-9 and b.z < a.z + a.height - 1e-9
            )
            testcase.assertFalse(overlap, f"{a} overlaps {b}")


class HelperTests(SimpleTestCase):
    def test_item_fits_alone_exact(self):
        self.assertTrue(item_fits_box_alone(item(l=10, w=10, h=10), box()))

    def test_item_fits_alone_needs_rotation(self):
        self.assertTrue(item_fits_box_alone(item(l=5, w=5, h=40), box(l=40, w=10, h=10)))

    def test_item_too_long_in_every_orientation(self):
        self.assertFalse(item_fits_box_alone(item(l=30, w=1, h=1), box()))

    def test_weight_boundary_is_inclusive(self):
        self.assertTrue(fits_weight([item(wt=5), item(wt=5)], box(max_w=10)))
        self.assertFalse(fits_weight([item(wt=5), item(wt=5.01)], box(max_w=10)))


class PackItemsTests(SimpleTestCase):
    def test_single_item_exact_fit(self):
        b = box()
        placements = pack_items([item(l=10, w=10, h=10)], b)
        assert_valid_packing(self, placements, b, 1)

    def test_two_cubes_side_by_side(self):
        b = box(l=20, w=10, h=10)
        placements = pack_items([item(l=10, w=10, h=10), item(l=10, w=10, h=10)], b)
        assert_valid_packing(self, placements, b, 2)

    def test_three_cubes_do_not_fit_when_volume_too_small(self):
        b = box(l=25, w=10, h=10)
        self.assertIsNone(pack_items([item(l=10, w=10, h=10)] * 3, b))

    def test_volume_fits_but_shape_blocks(self):
        # Two 6x6x6 cubes (432) fit by volume in 10x10x10 (1000) but not geometrically.
        b = box()
        self.assertIsNone(pack_items([item(l=6, w=6, h=6)] * 2, b))

    def test_rotation_is_used(self):
        b = box(l=40, w=10, h=10)
        placements = pack_items([item(l=10, w=10, h=40)], b)
        assert_valid_packing(self, placements, b, 1)

    def test_stacking_uses_height(self):
        b = box(l=20, w=13, h=10)
        placements = pack_items([item(l=20, w=13, h=3)] * 3, b)
        assert_valid_packing(self, placements, b, 3)

    def test_random_packings_are_always_valid(self):
        """Whenever the heuristic claims success, the result must be a real packing."""
        rng = random.Random(1234)
        checked = 0
        for _ in range(300):
            b = box(l=rng.randint(15, 40), w=rng.randint(15, 40), h=rng.randint(15, 40))
            items = [
                item(f"i{k}", rng.randint(1, 15), rng.randint(1, 15), rng.randint(1, 15))
                for k in range(rng.randint(1, 8))
            ]
            placements = pack_items(items, b)
            if placements is not None:
                assert_valid_packing(self, placements, b, len(items))
                checked += 1
        self.assertGreater(checked, 50)  # make sure the test actually exercised packings


class SelectBoxTests(SimpleTestCase):
    def test_picks_cheapest_fitting_box(self):
        boxes = [box("big", 30, 30, 30, 20, "5.00"), box("small", 10, 10, 10, 5, "1.00")]
        result = select_box([item(l=5, w=5, h=5, wt=1)], boxes)
        self.assertEqual(result.box.name, "small")

    def test_skips_box_that_is_too_light(self):
        boxes = [box("weak", 30, 30, 30, 1, "1.00"), box("strong", 30, 30, 30, 20, "2.00")]
        result = select_box([item(wt=5)], boxes)
        self.assertEqual(result.box.name, "strong")

    def test_skips_box_that_is_too_small(self):
        boxes = [box("tiny", 2, 2, 2, 10, "0.10"), box("ok", 10, 10, 10, 10, "1.00")]
        result = select_box([item(l=5, w=5, h=5)], boxes)
        self.assertEqual(result.box.name, "ok")

    def test_cost_tie_prefers_smaller_volume(self):
        boxes = [box("larger", 20, 20, 20, 10, "1.00"), box("smaller", 10, 10, 10, 10, "1.00")]
        result = select_box([item(l=5, w=5, h=5)], boxes)
        self.assertEqual(result.box.name, "smaller")

    def test_full_tie_is_deterministic_by_name(self):
        boxes = [box("b", cost="1.00"), box("a", cost="1.00")]
        self.assertEqual(select_box([item()], boxes).box.name, "a")

    def test_cheaper_box_is_not_always_the_smaller_one(self):
        boxes = [box("small-pricey", 10, 10, 10, 10, "3.00"), box("big-cheap", 20, 20, 20, 10, "1.00")]
        self.assertEqual(select_box([item()], boxes).box.name, "big-cheap")

    def test_returns_none_when_nothing_fits(self):
        self.assertIsNone(select_box([item(l=50, w=50, h=50)], [box()]))

    def test_returns_none_with_no_boxes(self):
        self.assertIsNone(select_box([item()], []))

    def test_overweight_order(self):
        self.assertIsNone(select_box([item(wt=6), item(wt=6)], [box(max_w=10)]))

    def test_recommendation_summary_values(self):
        result = select_box([item(l=2, w=5, h=10, wt=2.5)], [box()])
        self.assertAlmostEqual(result.total_weight, 2.5)
        self.assertAlmostEqual(result.total_item_volume, 100.0)
        self.assertAlmostEqual(result.fill_ratio, 0.1)

    def test_empty_order_rejected(self):
        with self.assertRaises(InvalidInput):
            select_box([], [box()])

    def test_non_positive_item_rejected(self):
        with self.assertRaises(InvalidInput):
            select_box([item(l=0)], [box()])
        with self.assertRaises(InvalidInput):
            select_box([item(wt=-1)], [box()])

    def test_non_positive_box_rejected(self):
        with self.assertRaises(InvalidInput):
            select_box([item()], [box(l=0)])

    def test_negative_cost_rejected(self):
        with self.assertRaises(InvalidInput):
            select_box([item()], [box(cost="-1.00")])


class ExplainNoFitTests(SimpleTestCase):
    def test_no_boxes(self):
        self.assertIn("No boxes", explain_no_fit([item()], []))

    def test_weight_reason(self):
        self.assertIn("weighs", explain_no_fit([item(wt=99)], [box(max_w=10)]))

    def test_oversize_reason(self):
        msg = explain_no_fit([item("Banner", l=99, w=1, h=1)], [box()])
        self.assertIn("Banner", msg)
        self.assertIn("too large", msg)

    def test_combined_reason(self):
        msg = explain_no_fit([item(l=6, w=6, h=6)] * 2, [box()])
        self.assertIn("no single box", msg)
