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
