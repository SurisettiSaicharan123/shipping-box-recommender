"""Box selection logic.

This module is pure Python (no Django imports) so it can be unit tested quickly.

Approach
--------
For an order (a list of items) and a list of candidate boxes:

1. Weight filter: total item weight must be <= box.max_weight.
2. Volume filter: total item volume must be <= box internal volume.
3. Packing check: items are placed one at a time using a *guillotine*
   heuristic. Free space starts as the whole box. Each item is put in the
   corner of the smallest free space it fits into (trying all 6 rotations),
   and the leftover space is split into 3 non-overlapping free spaces.
4. Among boxes that pass, choose the cheapest; ties go to the smaller
   volume, then to the name (so results are deterministic).

Guarantees and limits
---------------------
* If `pack_items` returns placements, the items really fit (no overlaps, all
  inside the box). This is what keeps recommendations safe.
* It is a heuristic, not an exact bin-packing solver. In rare tight cases a
  valid packing exists that the heuristic misses, so a box may be rejected
  even though a cleverer arrangement would fit. This errs on the side of
  recommending a slightly larger box, never one that is too small.
* Items are treated as rigid cuboids, may be rotated to any of the 6
  orientations, and no padding/void-fill is modelled.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from itertools import permutations
from typing import Optional, Sequence

EPS = 1e-9


@dataclass(frozen=True)
class ItemSpec:
    name: str
    length: float
    width: float
    height: float
    weight: float

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height


@dataclass(frozen=True)
class BoxSpec:
    name: str
    length: float
    width: float
    height: float
    max_weight: float
    cost: Decimal

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height


@dataclass(frozen=True)
class Placement:
    item_name: str
    x: float
    y: float
    z: float
    length: float  # extent along x after rotation
    width: float  # extent along y after rotation
    height: float  # extent along z after rotation


@dataclass
class Recommendation:
    box: BoxSpec
    total_weight: float
    total_item_volume: float
    fill_ratio: float
    placements: list[Placement] = field(default_factory=list)


class InvalidInput(ValueError):
    """Raised when items or boxes contain impossible values."""


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
def _validate_items(items: Sequence[ItemSpec]) -> None:
    for it in items:
        if min(it.length, it.width, it.height, it.weight) <= 0:
            raise InvalidInput(f"Item '{it.name}' must have positive dimensions and weight.")


def _validate_boxes(boxes: Sequence[BoxSpec]) -> None:
    for b in boxes:
        if min(b.length, b.width, b.height, b.max_weight) <= 0:
            raise InvalidInput(f"Box '{b.name}' must have positive dimensions and max weight.")
        if b.cost < 0:
            raise InvalidInput(f"Box '{b.name}' cannot have a negative cost.")


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------
def _orientations(item: ItemSpec) -> list[tuple[float, float, float]]:
    """All distinct (l, w, h) orientations of the item (up to 6)."""
    return sorted(set(permutations((item.length, item.width, item.height))))


def item_fits_box_alone(item: ItemSpec, box: BoxSpec) -> bool:
    """True if the item fits in the empty box in at least one rotation."""
    return any(
        l <= box.length + EPS and w <= box.width + EPS and h <= box.height + EPS
        for l, w, h in _orientations(item)
    )


def fits_weight(items: Sequence[ItemSpec], box: BoxSpec) -> bool:
    return sum(i.weight for i in items) <= box.max_weight + EPS


def pack_items(items: Sequence[ItemSpec], box: BoxSpec) -> Optional[list[Placement]]:
    """Try to pack all items into the box. Returns placements, or None."""
    # Largest items first gives the heuristic its best chance.
    ordered = sorted(items, key=lambda i: (-i.volume, -max(i.length, i.width, i.height), i.name))

    # A free space is (x, y, z, length, width, height).
    free: list[tuple[float, float, float, float, float, float]] = [
        (0.0, 0.0, 0.0, box.length, box.width, box.height)
    ]
    placements: list[Placement] = []

    for item in ordered:
        best = None  # (space_volume, space_index, orientation)
        for idx, (_, _, _, sl, sw, sh) in enumerate(free):
            for l, w, h in _orientations(item):
                if l <= sl + EPS and w <= sw + EPS and h <= sh + EPS:
                    key = (sl * sw * sh, idx, (l, w, h))
                    if best is None or key < best:
                        best = key
                    break  # first orientation that fits this space is enough
        if best is None:
            return None

        _, idx, (l, w, h) = best
        x, y, z, sl, sw, sh = free.pop(idx)
        placements.append(Placement(item.name, x, y, z, l, w, h))

        # Split the remaining space into three disjoint pieces.
        candidates = [
            (x + l, y, z, sl - l, sw, sh),  # to the right of the item
            (x, y + w, z, l, sw - w, sh),  # in front of the item
            (x, y, z + h, l, w, sh - h),  # above the item
        ]
        for space in candidates:
            if space[3] > EPS and space[4] > EPS and space[5] > EPS:
                free.append(space)

    return placements


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def select_box(items: Sequence[ItemSpec], boxes: Sequence[BoxSpec]) -> Optional[Recommendation]:
    """Return the cheapest box that fits every item, or None if none does."""
    if not items:
        raise InvalidInput("An order must contain at least one item.")
    _validate_items(items)
    _validate_boxes(boxes)

    total_weight = sum(i.weight for i in items)
    total_volume = sum(i.volume for i in items)

    candidates: list[tuple[Decimal, float, str, BoxSpec, list[Placement]]] = []
    for box in boxes:
        if not fits_weight(items, box):
            continue
        if total_volume > box.volume + EPS:
            continue
        if not all(item_fits_box_alone(i, box) for i in items):
            continue
        placements = pack_items(items, box)
        if placements is not None:
            candidates.append((box.cost, box.volume, box.name, box, placements))

    if not candidates:
        return None

    candidates.sort(key=lambda c: (c[0], c[1], c[2]))
    _, _, _, best_box, best_placements = candidates[0]
    return Recommendation(
        box=best_box,
        total_weight=total_weight,
        total_item_volume=total_volume,
        fill_ratio=total_volume / best_box.volume,
        placements=best_placements,
    )


def explain_no_fit(items: Sequence[ItemSpec], boxes: Sequence[BoxSpec]) -> str:
    """Human-readable reason why select_box found nothing."""
    if not boxes:
        return "No boxes are configured."
    total_weight = sum(i.weight for i in items)
    heaviest_capacity = max(b.max_weight for b in boxes)
    if total_weight > heaviest_capacity + EPS:
        return (
            f"Order weighs {total_weight:g} kg, more than the largest box capacity "
            f"({heaviest_capacity:g} kg). Consider splitting the order."
        )
    for item in items:
        if not any(item_fits_box_alone(item, b) for b in boxes):
            return f"Item '{item.name}' is too large for every available box."
    return (
        "Every item fits a box on its own, but no single box can hold the whole order "
        "within its size and weight limits. Consider splitting the order."
    )
