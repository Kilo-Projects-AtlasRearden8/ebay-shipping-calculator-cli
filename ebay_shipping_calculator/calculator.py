"""Offline eBay shipping cost estimation.

Estimates what a package might cost to ship using common eBay calculated
shipping services, from weight, dimensions, and service tier only.

No API keys, no network calls, no personal data. Everything is local. The
numbers are planning estimates based on published rate brackets, not quotes:
actual eBay shipping depends on the carrier, service, package type, zones, and
surcharges. Update RATE_TABLES when carrier prices change.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass
from typing import Optional

DIM_DIVISOR = 166.0  # cubic inches per pound (standard dim-weight divisor)
OZ_PER_LB = 16

TIER_FIRST_CLASS = "first_class"
TIER_GROUND_ADVANTAGE = "ground_advantage"
TIER_PRIORITY_MAIL = "priority_mail"
TIER_PRIORITY_MAIL_EXPRESS = "priority_mail_express"

TIER_ORDER = (
    TIER_FIRST_CLASS,
    TIER_GROUND_ADVANTAGE,
    TIER_PRIORITY_MAIL,
    TIER_PRIORITY_MAIL_EXPRESS,
)

TIER_LABELS = {
    TIER_FIRST_CLASS: "First Class Package",
    TIER_GROUND_ADVANTAGE: "Ground Advantage",
    TIER_PRIORITY_MAIL: "Priority Mail",
    TIER_PRIORITY_MAIL_EXPRESS: "Priority Mail Express",
}

MAX_WEIGHT_OZ = {
    TIER_FIRST_CLASS: 15.99,
    TIER_GROUND_ADVANTAGE: 70 * OZ_PER_LB,
    TIER_PRIORITY_MAIL: 70 * OZ_PER_LB,
    TIER_PRIORITY_MAIL_EXPRESS: 70 * OZ_PER_LB,
}

# Base rate brackets: (max billable weight in oz, estimated price in USD),
# sorted ascending. First Class stops at 15.99 oz; the other tiers continue
# per pound above the last bracket up to the 70 lb maximum.
_BRACKETS = {
    TIER_FIRST_CLASS: [
        (4, 4.20),
        (8, 5.20),
        (12, 6.10),
        (15.99, 7.10),
    ],
    TIER_GROUND_ADVANTAGE: [
        (4, 4.75),
        (8, 5.50),
        (12, 6.75),
        (16, 7.85),
    ],
    TIER_PRIORITY_MAIL: [
        (16, 9.35),
        (32, 12.05),
        (48, 14.75),
        (64, 17.45),
    ],
    TIER_PRIORITY_MAIL_EXPRESS: [
        (16, 28.75),
        (32, 31.10),
        (48, 33.55),
        (64, 36.00),
    ],
}

_PER_LB_ABOVE_BRACKET = {
    TIER_GROUND_ADVANTAGE: 0.80,
    TIER_PRIORITY_MAIL: 1.10,
    TIER_PRIORITY_MAIL_EXPRESS: 1.60,
}


def _build_table(tier: str) -> list:
    rows = list(_BRACKETS[tier])
    if tier not in _PER_LB_ABOVE_BRACKET:
        return rows
    per_lb = _PER_LB_ABOVE_BRACKET[tier]
    last_w, last_p = rows[-1]
    w = last_w + OZ_PER_LB
    while w <= MAX_WEIGHT_OZ[tier]:
        last_p = round(last_p + per_lb, 2)
        rows.append((w, last_p))
        w += OZ_PER_LB
    return rows


RATE_TABLES = {tier: _build_table(tier) for tier in TIER_ORDER}


def dimensional_weight_oz(length_in: float, width_in: float, height_in: float) -> float:
    """Dimensional weight in ounces: (L x W x H) / 166 x 16."""
    return (length_in * width_in * height_in) / DIM_DIVISOR * OZ_PER_LB


def billable_weight_oz(
    actual_weight_oz: float,
    dims: Optional[tuple] = None,
) -> float:
    """Billable weight is the greater of actual and dimensional weight."""
    weight = actual_weight_oz
    if dims is not None:
        weight = max(weight, dimensional_weight_oz(*dims))
    return weight


@dataclass
class MarginHint:
    estimated_shipping_usd: float
    shipping_charged_usd: Optional[float]
    item_price_usd: Optional[float]
    shipping_margin_usd: Optional[float]
    shipping_as_percent_of_item: Optional[float]
    hint: str


def shipping_margin_hint(
    estimated_shipping_usd: float,
    shipping_charged_usd: Optional[float] = None,
    item_price_usd: Optional[float] = None,
) -> MarginHint:
    """Plain-English hint about whether a shipping charge covers its cost."""
    estimated = round(estimated_shipping_usd, 2)
    margin: Optional[float] = None
    if shipping_charged_usd is not None:
        margin = round(shipping_charged_usd - estimated, 2)

    pct: Optional[float] = None
    if item_price_usd and item_price_usd > 0:
        pct = round(estimated / item_price_usd * 100, 1)

    if shipping_charged_usd is None:
        hint = (
            f"Estimated shipping is {format_money(estimated)}. Charge the buyer "
            "at least this much, or build it into the item price so it does "
            "not eat your profit."
        )
    elif margin is not None and margin < 0:
        hint = (
            f"You charged {format_money(shipping_charged_usd)} for shipping "
            f"but it costs about {format_money(estimated)} — you absorb "
            f"{format_money(-margin)} per order. Consider raising the shipping "
            "charge or the item price."
        )
    elif margin is not None and margin == 0:
        hint = (
            f"Your {format_money(shipping_charged_usd)} shipping charge covers "
            f"the estimated {format_money(estimated)} cost exactly. Leave room "
            "for supplies and handling."
        )
    else:
        hint = (
            f"You charged {format_money(shipping_charged_usd)} against an "
            f"estimated {format_money(estimated)} cost, keeping "
            f"{format_money(margin)} for supplies and handling."
        )

    if pct is not None:
        if pct < 20:
            hint += f" Shipping is {pct}% of the item price."
        else:
            hint += (
                f" At {pct}% of the item price, shipping is a big share — "
                "consider a flat shipping fee or free-shipping pricing."
            )

    return MarginHint(
        estimated_shipping_usd=estimated,
        shipping_charged_usd=shipping_charged_usd,
        item_price_usd=item_price_usd,
        shipping_margin_usd=margin,
        shipping_as_percent_of_item=pct,
        hint=hint,
    )


def format_money(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"${value:,.2f}"


def rate_for(tier: str, weight_oz: float) -> tuple:
    """Return (price_usd, note) for the first bracket covering weight_oz."""
    table = RATE_TABLES[tier]
    max_weights = [row[0] for row in table]
    idx = bisect.bisect_left(max_weights, weight_oz)
    if idx >= len(table):
        return None, (
            f"{weight_oz / OZ_PER_LB:.1f} lb exceeds the {tier} maximum "
            f"({MAX_WEIGHT_OZ[tier] / OZ_PER_LB:.0f} lb). Request a custom quote."
        )
    return table[idx][1], ""


def estimate_shipping(
    weight_oz: float,
    tier: str = TIER_GROUND_ADVANTAGE,
    dims: Optional[tuple] = None,
    item_price_usd: Optional[float] = None,
    shipping_charged_usd: Optional[float] = None,
) -> dict:
    """Estimate shipping cost and return a plain-English result dict."""
    if weight_oz <= 0:
        raise ValueError("weight_oz must be greater than zero")
    if tier not in RATE_TABLES:
        raise ValueError(f"Unknown service tier: {tier}")

    billable = billable_weight_oz(weight_oz, dims)
    dim_weight = dimensional_weight_oz(*dims) if dims else None

    cost, note = rate_for(tier, billable)
    applicable = cost is not None

    if applicable and dim_weight is not None and dim_weight > weight_oz:
        note = "Priced at dimensional weight (package is large and light)."

    result = {
        "tier": tier,
        "tier_label": TIER_LABELS[tier],
        "weight_oz": round(weight_oz, 2),
        "billable_weight_oz": round(billable, 2),
        "dimensional_weight_oz": round(dim_weight, 2) if dim_weight else None,
        "estimated_cost_usd": round(cost, 2) if cost is not None else None,
        "applicable": applicable,
        "note": note,
        "margin": None,
    }

    if applicable:
        result["margin"] = shipping_margin_hint(
            cost, shipping_charged_usd, item_price_usd
        )

    return result
