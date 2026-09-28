"""Glue between Django Orders and the pure packing logic."""
from typing import Optional

from ..models import Box, Order
from .packing import InvalidInput, Recommendation, explain_no_fit, select_box

MAX_TOTAL_UNITS = 500  # keeps worst-case packing time bounded


def recommend_for_order(order: Order) -> Optional[Recommendation]:
    """Work out the best box for `order`, save it on the order, and return the result.

    On failure (no items, too many units, nothing fits) `order.recommended_box` is
    cleared and `order.recommendation_message` explains why.
    """
    specs = []
    for line in order.items.select_related("product"):
        specs.extend([line.product.to_spec()] * line.quantity)

    boxes = list(Box.objects.all())
    box_specs = [b.to_spec() for b in boxes]

    result = None
    if not specs:
        message = "Order has no items."
    elif len(specs) > MAX_TOTAL_UNITS:
        message = f"At most {MAX_TOTAL_UNITS} units per order are supported."
    else:
        try:
            result = select_box(specs, box_specs)
        except InvalidInput as exc:
            message = str(exc)
        else:
            if result is None:
                message = explain_no_fit(specs, box_specs)
            else:
                message = (
                    f"Use '{result.box.name}' (cost {result.box.cost}, "
                    f"{result.fill_ratio:.0%} full by volume)."
                )

    by_name = {b.name: b for b in boxes}
    order.recommended_box = by_name[result.box.name] if result else None
    order.recommendation_message = message
    order.save(update_fields=["recommended_box", "recommendation_message"])
    return result
