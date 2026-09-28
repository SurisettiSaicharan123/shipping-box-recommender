import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Box, Product
from .services.packing import InvalidInput, explain_no_fit, select_box

MAX_LINES = 200
MAX_TOTAL_UNITS = 500  # keeps worst-case packing time bounded


def _error(code: str, message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"error": code, "message": message}, status=status)


def _parse_items(payload):
    """Validate the request body. Returns (lines, error_response)."""
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


@csrf_exempt
@require_POST
def recommend_box(request):
    """POST /api/recommend-box/

    Body: {"items": [{"product_id": 1, "quantity": 2}, ...]}
    """
    try:
        payload = json.loads(request.body or b"")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error("invalid_json", "Request body is not valid JSON.")

    quantities, err = _parse_items(payload)
    if err:
        return err

    products = Product.objects.in_bulk(list(quantities))
    missing = sorted(set(quantities) - set(products))
    if missing:
        return _error("unknown_product", f"Unknown product id(s): {missing}", status=404)

    item_specs = []
    for pid, qty in quantities.items():
        spec = products[pid].to_spec()
        item_specs.extend([spec] * qty)

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

    return JsonResponse(
        {
            "recommended_box": {
                "name": result.box.name,
                "internal_dimensions_cm": [result.box.length, result.box.width, result.box.height],
                "max_weight_kg": result.box.max_weight,
                "cost": str(result.box.cost),
            },
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
