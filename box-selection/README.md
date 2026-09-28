# AI-Assisted Box Selection System

A small Django service that recommends the cheapest shipping box that can hold an order.

## How it works

`POST /api/recommend-box/` takes a list of `{product_id, quantity}` lines. For each box, the
service checks, in order:

1. **Weight**: total order weight <= box max weight.
2. **Volume**: total item volume <= box internal volume.
3. **Each item fits alone** in at least one of its 6 rotations.
4. **Packing**: a guillotine heuristic places items one by one (largest first) into the
   smallest free space that fits, splitting leftover space into 3 disjoint regions.

Among boxes that pass, the **cheapest** wins; ties go to the **smaller volume**, then the name.
If nothing fits, the API returns `422` with a reason (too heavy, item too large, or
"each item fits but not together").

The logic lives in `boxes/services/packing.py` and has no Django imports, so it is unit tested
without a database.

### Assumptions and limitations

- Items are rigid cuboids; any of the 6 rotations is allowed. No padding or void fill is modelled.
- Units: dimensions in cm, weight in kg, cost in a single currency.
- The packing step is a **heuristic**. When it says items fit, they truly do (verified by a
  randomized no-overlap / in-bounds test). It can occasionally reject a tight arrangement that a
  smarter algorithm would find, so it may recommend a slightly larger box, never a too-small one.
- Limits to bound runtime: at most 200 order lines and 500 units per request.
- The order is not persisted; the endpoint is a pure recommendation (products and boxes are
  managed in the Django admin).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata sample_data      # 6 products, 4 boxes
python manage.py createsuperuser           # optional, for /admin/
python manage.py runserver
```

## Example

```bash
curl -X POST http://localhost:8000/api/recommend-box/ \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 2, "quantity": 6}]}'
```

```json
{
  "recommended_box": {"name": "Medium", "internal_dimensions_cm": [40.0, 30.0, 20.0],
                      "max_weight_kg": 10.0, "cost": "1.50"},
  "order_summary": {"total_units": 6, "total_weight_kg": 2.4,
                    "total_item_volume_cm3": 6000.0, "box_fill_ratio": 0.25},
  "placements": [{"item": "Coffee Mug", "position_cm": [0.0, 0.0, 0.0], "size_cm": [10.0, 10.0, 10.0]}, "..."]
}
```

Errors: `400` malformed input, `404` unknown product, `405` wrong method,
`422` no box fits (or invalid product/box data).

## Tests

```bash
python manage.py test -v 2
```

61 tests: packing algorithm (rotation, stacking, ties, weight limits, randomized validity),
models (validation and DB constraints), and the API (success, no-fit, validation errors).
CI runs the same on every push (`.github/workflows/tests.yml`). See `TEST_OUTPUT.md`.

## Project layout

```
config/            Django settings, urls, wsgi
boxes/models.py    Product, Box
boxes/services/    packing.py (pure-Python algorithm)
boxes/views.py     POST /api/recommend-box/
boxes/fixtures/    sample_data.json
boxes/tests/       test_packing.py, test_models.py, test_api.py
```
