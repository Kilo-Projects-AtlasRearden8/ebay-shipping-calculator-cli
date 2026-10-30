"""Local JSON storage for shipping quotes."""

from __future__ import annotations

import csv
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

DEFAULT_STORAGE_PATH = "shipments.json"


class Storage:
    """Append-only JSON store of shipping quote records."""

    def __init__(self, path: str = DEFAULT_STORAGE_PATH):
        self.path = path
        self.records = self._load()

    def _load(self) -> list:
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.records, fh, indent=2)

    def add(self, record: dict) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        entry.update(record)
        self.records.append(entry)
        self.save()
        return entry

    def list(self) -> list:
        return list(self.records)

    def export_csv(self, out_path: str) -> int:
        fields = [
            "id",
            "timestamp",
            "item",
            "tier",
            "tier_label",
            "weight_oz",
            "billable_weight_oz",
            "length_in",
            "width_in",
            "height_in",
            "dimensional_weight_oz",
            "estimated_cost_usd",
            "item_price_usd",
            "shipping_charged_usd",
            "shipping_margin_usd",
            "shipping_as_percent_of_item",
        ]
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            count = 0
            for record in self.records:
                row = {field: record.get(field) for field in fields}
                writer.writerow(row)
                count += 1
        return count
