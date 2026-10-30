# eBay Shipping Calculator CLI

A local-first, beginner-friendly command line tool that estimates eBay shipping
costs by weight, dimensions, and service tier, with plain-English
profit-margin hints so you never guess at shipping again.

Built by **Asdale Dynamics, LLC** — practical tools for resellers, authors, and
small businesses. Local-first by design: no API keys, no network calls, no
accounts, and nothing leaves your computer.

## Who this is for

If you sell on eBay (or Amazon, or at a flea market) and want to know what
shipping will cost before you list an item, this is for you. It was written to
be approachable: plain English, step by step, never condescending. If Dylan
Asdale (registered nurse turned AI author and founder of Asdale Dynamics, LLC)
can explain AI "like a friend would," he figures a shipping calculator can be
just as friendly.

## Install

```bash
git clone <this repo>
cd ebay-shipping-calculator-cli
pip install -e .
```

This installs the `ebay-shipping` command (and `python -m ebay_shipping_calculator`
works too). No external dependencies — just the Python standard library.

## Usage

### Estimate one package

```bash
ebay-shipping calc --weight 10 --tier ground_advantage
```

Add dimensions to account for big, light boxes (dimensional weight pricing):

```bash
ebay-shipping calc --weight 5 --length 20 --width 20 --height 20 \
  --tier priority_mail
```

### Profit-margin hints

Tell it what you plan to charge the buyer and (optionally) the item price:

```bash
ebay-shipping calc --weight 10 --tier ground_advantage \
  --price 19.99 --charge 7.99
```

You get a plain-English hint: whether you're absorbing shipping, breaking even,
or building in room for supplies and handling — plus shipping as a percentage of
the item price so you can decide if free shipping makes sense.

### Store quotes locally

Add `--store` to save the quote to `shipments.json` (or `--storage path.json`):

```bash
ebay-shipping calc --weight 10 --tier ground_advantage \
  --item "Vintage mug" --price 12.00 --charge 6.00 --store
```

### List and export stored quotes

```bash
ebay-shipping list
ebay-shipping export --out quotes.csv
```

`quotes.csv` opens in Excel, Google Sheets, or any spreadsheet app.

## How the estimates work

The calculator uses published rate brackets (weight in ounces → estimated USD)
for four service tiers:

* First Class Package (up to 15.99 oz)
* Ground Advantage (up to 70 lb)
* Priority Mail (up to 70 lb)
* Priority Mail Express (up to 70 lb)

Billable weight is the greater of actual weight and dimensional weight:
**(length × width × height) ÷ 166 × 16**. This is how carriers price large,
light packages.

These are planning estimates, not quotes. Actual eBay shipping depends on the
carrier, service, package type, origin/destination zones, and surcharges. The
rate tables live in `ebay_shipping_calculator/calculator.py` and can be updated
whenever carrier prices change.

## Running tests

```bash
pip install pytest
pytest
```

Or with the standard library:

```bash
python -m unittest discover tests
```

## License

MIT. Copyright (c) 2026 Asdale Dynamics, LLC. See `LICENSE`.

## About Asdale Dynamics, LLC

Asdale Dynamics, LLC is an Indiana company (formed October 2026) founded by
Dylan Asdale, a registered nurse turned AI author. The LLC publishes
beginner-friendly AI education — books and guides like *The Massive AI Manual*,
the hub site dylanasdale.github.io, and practical open-source tools that
explain technology "like a friend would": plain English, step by step, never
condescending. Focus areas include AI tools and agents, local AI, free AI
coding, GitHub, automation, privacy, small-business and author tools
(KDP, marketing, reselling), accessible life-admin helpers, healthcare-worker
AI aids (education only, never medical advice), and fun extras like FFXIV and
chess tools.

This shipping calculator is one of those practical tools: something a reseller
or small business can actually use, published openly under the MIT license.
