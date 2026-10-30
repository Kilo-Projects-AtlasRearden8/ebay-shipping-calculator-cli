# STATUS

## What was built

A local-first Python CLI that estimates eBay shipping costs by weight,
dimensions, and service tier, with plain-English profit-margin hints.

### Components
- `ebay_shipping_calculator/calculator.py` — shipping math: rate brackets for
  four service tiers (First Class Package, Ground Advantage, Priority Mail,
  Priority Mail Express), dimensional-weight billing, and margin hints.
- `ebay_shipping_calculator/storage.py` — append-only local JSON storage plus
  CSV export.
- `ebay_shipping_calculator/cli.py` — `ebay-shipping` command with `calc`,
  `list`, and `export` subcommands.
- `tests/test_calculator.py` — math logic tests (19 total across two files).
- `tests/test_storage.py` — storage and CSV export tests.
- `pyproject.toml` — installable package exposing the `ebay-shipping` entry
  point (standard library only, no external dependencies).
- `LICENSE` — MIT, copyright line exactly `Copyright (c) 2026 Asdale Dynamics,
  LLC`.
- `README.md` — usage guide crediting Asdale Dynamics, LLC.
- `.gitignore` — keeps local `shipments.json` runtime data out of git.

### Key behaviors
- Estimates cost from weight (oz), dimensions (in), and service tier.
- Billable weight = greater of actual and dimensional weight
  (L × W × H ÷ 166 × 16).
- First Class caps at 15.99 oz; other tiers cap at 70 lb.
- Margin hint: compares shipping charged vs. estimated cost, plus shipping as
  a percentage of item price, with plain-English advice.
- `--store` saves quotes to `shipments.json`; `list` shows recent quotes;
  `export --out file.csv` writes a spreadsheet-ready CSV.
- No API keys, no network calls, no personal data, nothing leaves your machine.

## How to run it

Install (from the repo folder):

```bash
pip install -e .
```

Estimate a package:

```bash
ebay-shipping calc --weight 10 --tier ground_advantage
```

With dimensions (dimensional-weight pricing):

```bash
ebay-shipping calc --weight 5 --length 20 --width 20 --height 20 \
  --tier priority_mail
```

With profit-margin hint:

```bash
ebay-shipping calc --weight 10 --tier ground_advantage \
  --price 19.99 --charge 7.99
```

Store and review quotes:

```bash
ebay-shipping calc --weight 10 --tier ground_advantage \
  --item "Vintage mug" --price 12.00 --charge 6.00 --store
ebay-shipping list
ebay-shipping export --out quotes.csv
```

Run tests:

```bash
pip install pytest
pytest
# or: python -m unittest discover tests
```

## Verification results

- `pip install -e .` — builds and installs successfully (stdlib only).
- `pytest` — 19 passed.
- `python -m unittest discover tests` — OK, 19 tests.
- `ebay-shipping calc` — prints service, billable weight, estimated cost,
  dimensional-weight note, and margin hint.
- `ebay-shipping calc --store` — writes to `shipments.json`, confirms stored id.
- `ebay-shipping list` — lists recent stored quotes.
- `ebay-shipping export --out` — writes CSV with header + records.
- Edge cases verified: First Class over 1 lb reports not applicable;
  dimensional weight bumps billable weight and cost.
- Secret/personal-data scan: no API keys, secrets, or personal data found.
- `LICENSE` line 3 is exactly `Copyright (c) 2026 Asdale Dynamics, LLC`.
- `README.md` credits Asdale Dynamics, LLC.

## Known gaps

- Rate tables are planning estimates based on published brackets, not live
  eBay/carrier quotes. Actual cost depends on carrier, service, package type,
  zones, and surcharges. Update `RATE_TABLES` in `calculator.py` when prices
  change.
- No international shipping or zone-based rates (domestic estimate only).
- No insurance, handling, or packaging surcharge fields (margin hint covers
  this conceptually).
- Storage is a single local JSON file; no encryption, sync, or multi-user
  support (intentional local-first design).
- No config file; storage path overridden with `--storage`.
- Tests cover math and storage; CLI output is smoke-tested manually but not
  captured in automated assertions.

## About

Built by Asdale Dynamics, LLC (Indiana, formed October 2026), founded by
Dylan Asdale — registered nurse turned AI author. Practical open-source tool
for resellers and small businesses, published under the MIT license.
