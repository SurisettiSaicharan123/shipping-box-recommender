from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from .services.packing import BoxSpec, ItemSpec

POSITIVE = [MinValueValidator(0.0001)]


class Product(models.Model):
    """A sellable product. Dimensions in cm, weight in kg."""

    name = models.CharField(max_length=200, unique=True)
    length = models.FloatField(validators=POSITIVE)
    width = models.FloatField(validators=POSITIVE)
    height = models.FloatField(validators=POSITIVE)
    weight = models.FloatField(validators=POSITIVE)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(length__gt=0) & Q(width__gt=0) & Q(height__gt=0) & Q(weight__gt=0),
                name="product_positive_values",
            )
        ]

    def __str__(self):
        return self.name

    def to_spec(self) -> ItemSpec:
        return ItemSpec(
            name=self.name,
            length=self.length,
            width=self.width,
            height=self.height,
            weight=self.weight,
        )


class Box(models.Model):
    """A shipping box. Internal dimensions in cm, max weight in kg."""

    name = models.CharField(max_length=200, unique=True)
    length = models.FloatField(validators=POSITIVE, help_text="Internal length (cm)")
    width = models.FloatField(validators=POSITIVE, help_text="Internal width (cm)")
    height = models.FloatField(validators=POSITIVE, help_text="Internal height (cm)")
    max_weight = models.FloatField(validators=POSITIVE, help_text="Maximum weight capacity (kg)")
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ["cost", "name"]
        verbose_name_plural = "boxes"
        constraints = [
            models.CheckConstraint(
                condition=Q(length__gt=0) & Q(width__gt=0) & Q(height__gt=0) & Q(max_weight__gt=0),
                name="box_positive_values",
            )
        ]

    def __str__(self):
        return self.name

    def to_spec(self) -> BoxSpec:
        return BoxSpec(
            name=self.name,
            length=self.length,
            width=self.width,
            height=self.height,
            max_weight=self.max_weight,
            cost=Decimal(str(self.cost)),
        )


class Order(models.Model):
    """A customer order. The recommended box is filled in automatically."""

    created_at = models.DateTimeField(auto_now_add=True)
    recommended_box = models.ForeignKey(
        Box, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    recommendation_message = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Order #{self.pk}"

    @property
    def total_units(self) -> int:
        return sum(line.quantity for line in self.items.all())

    @property
    def total_weight(self) -> float:
        return sum(line.quantity * line.product.weight for line in self.items.select_related("product"))


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "product"], name="unique_product_per_order"),
            models.CheckConstraint(condition=Q(quantity__gte=1), name="orderitem_quantity_gte_1"),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
