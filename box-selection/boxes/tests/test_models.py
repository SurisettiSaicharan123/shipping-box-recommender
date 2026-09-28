from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from boxes.models import Box, Product


class ProductModelTests(TestCase):
    def test_to_spec(self):
        p = Product.objects.create(name="Mug", length=10, width=10, height=10, weight=0.4)
        spec = p.to_spec()
        self.assertEqual((spec.name, spec.length, spec.weight), ("Mug", 10, 0.4))

    def test_validation_rejects_zero_dimension(self):
        p = Product(name="Bad", length=0, width=1, height=1, weight=1)
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_database_rejects_negative_weight(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Product.objects.create(name="Bad", length=1, width=1, height=1, weight=-1)


class BoxModelTests(TestCase):
    def test_to_spec(self):
        b = Box.objects.create(name="S", length=10, width=10, height=10, max_weight=5, cost="1.25")
        spec = b.to_spec()
        self.assertEqual(spec.cost, Decimal("1.25"))
        self.assertEqual(spec.volume, 1000)

    def test_validation_rejects_negative_cost(self):
        b = Box(name="Bad", length=1, width=1, height=1, max_weight=1, cost=Decimal("-1"))
        with self.assertRaises(ValidationError):
            b.full_clean()

    def test_database_rejects_zero_max_weight(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Box.objects.create(name="Bad", length=1, width=1, height=1, max_weight=0, cost="1")
