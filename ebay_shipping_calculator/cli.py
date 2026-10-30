"""Command line interface for the eBay shipping calculator."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from .calculator import (
    TIER_GROUND_ADVANTAGE,
    TIER_ORDER,
    TIER_LABELS,
    estimate_shipping,
    format_money,
)
from .storage import DEFAULT_STORAGE_PATH, Storage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ebay-shipping",
        description=(
            "Estimate eBay shipping costs by weight, dimensions, and service "
            "tier. Local-first: no API keys, no network calls, no personal data."
        ),
    )
    parser.add_argument(
        "--storage",
        default=DEFAULT_STORAGE_PATH,
        help=f"Local JSON storage file (default: {DEFAULT_STORAGE_PATH})",
    )

    sub = parser.add_subparsers(dest="command")

    calc = sub.add_parser("calc", help="Estimate shipping cost for one package")
    calc.add_argument(
        "--weight", type=float, required=True, help="Package weight in ounces"
    )
    calc.add_argument(
        "--tier",
        choices=TIER_ORDER,
        default=TIER_GROUND_ADVANTAGE,
        help="Service tier (default: ground_advantage)",
    )
    calc.add_argument("--length", type=float, help="Package length in inches")
    calc.add_argument("--width", type=float, help="Package width in inches")
    calc.add_argument("--height", type=float, help="Package height in inches")
    calc.add_argument("--item", help="Item name (stored with the quote)")
    calc.add_argument(
        "--price", type=float, help="Item sale price in USD (for margin hint)"
    )
    calc.add_argument(
        "--charge",
        type=float,
        help="Amount charged to buyer for shipping in USD (for margin hint)",
    )
    calc.add_argument(
        "--store", action="store_true", help="Save this quote to local JSON storage"
    )

    list_p = sub.add_parser("list", help="List stored quotes")
    list_p.add_argument("--limit", type=int, default=20, help="Max records to show")

    exp = sub.add_parser("export", help="Export stored quotes to CSV")
    exp.add_argument("--out", required=True, help="Output CSV path")

    return parser


def _dims_from_args(args) -> Optional[tuple]:
    if args.length is None and args.width is None and args.height is None:
        return None
    if None in (args.length, args.width, args.height):
        print(
            "Error: --length, --width, and --height must all be provided together.",
            file=sys.stderr,
        )
        return False
    return (args.length, args.width, args.height)


def _format_margin(margin) -> str:
    if not margin:
        return ""
    lines = [f"Margin hint: {margin.hint}"]
    if margin.shipping_margin_usd is not None:
        lines.append(
            f"Shipping margin: {format_money(margin.shipping_margin_usd)}"
        )
    if margin.shipping_as_percent_of_item is not None:
        lines.append(
            f"Shipping as % of item price: {margin.shipping_as_percent_of_item}%"
        )
    return "\n".join(lines)


def cmd_calc(args) -> int:
    dims = _dims_from_args(args)
    if dims is False:
        return 2

    try:
        result = estimate_shipping(
            args.weight,
            tier=args.tier,
            dims=dims,
            item_price_usd=args.price,
            shipping_charged_usd=args.charge,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Service: {result['tier_label']}")
    print(
        f"Weight: {result['weight_oz']} oz -> billable "
        f"{result['billable_weight_oz']} oz"
    )
    if result["dimensional_weight_oz"] is not None:
        print(f"Dimensional weight: {result['dimensional_weight_oz']} oz")
    if result["applicable"]:
        print(f"Estimated cost: {format_money(result['estimated_cost_usd'])}")
        if result["note"]:
            print(f"Note: {result['note']}")
        print(_format_margin(result["margin"]))
    else:
        print(f"Estimated cost: not available — {result['note']}")

    if args.store:
        storage = Storage(args.storage)
        margin = result["margin"]
        record = {
            "item": args.item,
            "tier": result["tier"],
            "tier_label": result["tier_label"],
            "weight_oz": args.weight,
            "billable_weight_oz": result["billable_weight_oz"],
            "length_in": dims[0] if dims else None,
            "width_in": dims[1] if dims else None,
            "height_in": dims[2] if dims else None,
            "dimensional_weight_oz": result["dimensional_weight_oz"],
            "estimated_cost_usd": result["estimated_cost_usd"],
            "applicable": result["applicable"],
            "note": result["note"],
            "item_price_usd": args.price,
            "shipping_charged_usd": args.charge,
            "shipping_margin_usd": margin.shipping_margin_usd if margin else None,
            "shipping_as_percent_of_item": (
                margin.shipping_as_percent_of_item if margin else None
            ),
        }
        entry = storage.add(record)
        print(f"Stored (id {entry['id'][:8]}) in {args.storage}")
    return 0


def cmd_list(args) -> int:
    storage = Storage(args.storage)
    records = storage.list()
    if not records:
        print("No stored quotes yet.")
        return 0
    for record in records[-args.limit :]:
        margin = record.get("shipping_margin_usd")
        margin_txt = f", margin {format_money(margin)}" if margin is not None else ""
        print(
            f"{record['id'][:8]} {record['timestamp'][:10]} "
            f"{record.get('item', '(unnamed)')} "
            f"{record.get('tier_label', record.get('tier'))} "
            f"{format_money(record.get('estimated_cost_usd'))}{margin_txt}"
        )
    return 0


def cmd_export(args) -> int:
    storage = Storage(args.storage)
    count = storage.export_csv(args.out)
    print(f"Exported {count} record(s) to {args.out}")
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "calc":
        return cmd_calc(args)
    if args.command == "list":
        return cmd_list(args)
    if args.command == "export":
        return cmd_export(args)
    parser.print_help()
    return 0
