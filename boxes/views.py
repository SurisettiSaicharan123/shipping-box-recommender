import json

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Box, Order, OrderItem, Product
from .services.orders import MAX_TOTAL_UNITS, recommend_for_order
from .services.packing import InvalidInput, explain_no_fit, select_box

MAX_LINES = 200


def _error(code: str, message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"error": code, "message": message}, status=status)


def _load_json(request):
    """Returns (payload, error_response)."""
    try:
        return json.loads(request.body or b""), None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, _error("invalid_json", "Request body is not valid JSON.")


def _parse_items(payload):
    """Validate the request body. Returns ({product_id: quantity}, error_response)."""
    if not isinstance(payload, dict):
        return None, _error("invalid_body", "Body must be a JSON object.")
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        return None, _error("invalid_items", "'items' must be a non-empty list.")
    if len(items) > MAX_LINES:
        return None, _error("too_many_lines", f"At most {MAX_LINES} order lines are allowed.")

    quantities: dict[int, int] = {}
    for idx, line in enumerate(items):
        if not isinstance(line, dict):
            return None, _error("invalid_item", f"items[{idx}] must be an object.")
        pid, qty = line.get("product_id"), line.get("quantity")
        # bool is a subclass of int in Python, so reject it explicitly.
        if isinstance(pid, bool) or not isinstance(pid, int):
            return None, _error("invalid_item", f"items[{idx}].product_id must be an integer.")
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
            return None, _error("invalid_item", f"items[{idx}].quantity must be an integer >= 1.")
        quantities[pid] = quantities.get(pid, 0) + qty

    if sum(quantities.values()) > MAX_TOTAL_UNITS:
        return None, _error(
            "too_many_units", f"At most {MAX_TOTAL_UNITS} units per order are supported."
        )
    return quantities, None


def _load_products(quantities):
    """Returns (products_by_id, error_response)."""
    products = Product.objects.in_bulk(list(quantities))
    missing = sorted(set(quantities) - set(products))
    if missing:
        return None, _error("unknown_product", f"Unknown product id(s): {missing}", status=404)
    return products, None


def _box_payload(name, dims, max_weight, cost):
    return {
        "name": name,
        "internal_dimensions_cm": list(dims),
        "max_weight_kg": max_weight,
        "cost": str(cost),
    }


# --------------------------------------------------------------------------
# Stateless recommendation: POST /api/recommend-box/
# --------------------------------------------------------------------------
@csrf_exempt
@require_POST
def recommend_box(request):
    """Body: {"items": [{"product_id": 1, "quantity": 2}, ...]}  (nothing is saved)"""
    payload, err = _load_json(request)
    if err:
        return err
    quantities, err = _parse_items(payload)
    if err:
        return err
    products, err = _load_products(quantities)
    if err:
        return err

    item_specs = []
    for pid, qty in quantities.items():
        item_specs.extend([products[pid].to_spec()] * qty)
    box_specs = [b.to_spec() for b in Box.objects.all()]

    try:
        result = select_box(item_specs, box_specs)
    except InvalidInput as exc:
        return _error("invalid_data", str(exc), status=422)

    if result is None:
        return JsonResponse(
            {"error": "no_box_fits", "message": explain_no_fit(item_specs, box_specs)},
            status=422,
        )

    box = result.box
    return JsonResponse(
        {
            "recommended_box": _box_payload(
                box.name, (box.length, box.width, box.height), box.max_weight, box.cost
            ),
            "order_summary": {
                "total_units": len(item_specs),
                "total_weight_kg": round(result.total_weight, 4),
                "total_item_volume_cm3": round(result.total_item_volume, 4),
                "box_fill_ratio": round(result.fill_ratio, 4),
            },
            "placements": [
                {
                    "item": p.item_name,
                    "position_cm": [p.x, p.y, p.z],
                    "size_cm": [p.length, p.width, p.height],
                }
                for p in result.placements
            ],
        }
    )


# --------------------------------------------------------------------------
# Orders: create an order (and get its box) or fetch it later
# --------------------------------------------------------------------------
def _order_payload(order: Order) -> dict:
    lines = list(order.items.select_related("product"))
    box = order.recommended_box
    return {
        "order_id": order.pk,
        "created_at": order.created_at.isoformat(),
        "items": [
            {"product_id": l.product_id, "product": l.product.name, "quantity": l.quantity}
            for l in lines
        ],
        "total_units": sum(l.quantity for l in lines),
        "total_weight_kg": round(sum(l.quantity * l.product.weight for l in lines), 4),
        "recommended_box": (
            _box_payload(box.name, (box.length, box.width, box.height), box.max_weight, box.cost)
            if box
            else None
        ),
        "message": order.recommendation_message,
    }


@csrf_exempt
@require_POST
def create_order(request):
    """POST /api/orders/  Body: {"items": [{"product_id": 1, "quantity": 2}, ...]}

    Saves the order and returns it with its recommended box. If no box fits, the order
    is still saved (201) with "recommended_box": null and a "message" explaining why.
    """
    payload, err = _load_json(request)
    if err:
        return err
    quantities, err = _parse_items(payload)
    if err:
        return err
    products, err = _load_products(quantities)
    if err:
        return err

    with transaction.atomic():
        order = Order.objects.create()
        OrderItem.objects.bulk_create(
            OrderItem(order=order, product=products[pid], quantity=qty)
            for pid, qty in quantities.items()
        )
        recommend_for_order(order)
    return JsonResponse(_order_payload(order), status=201)


@require_GET
def order_detail(request, pk: int):
    """GET /api/orders/<id>/"""
    order = Order.objects.select_related("recommended_box").filter(pk=pk).first()
    if order is None:
        return _error("not_found", f"Order {pk} does not exist.", status=404)
    return JsonResponse(_order_payload(order))
