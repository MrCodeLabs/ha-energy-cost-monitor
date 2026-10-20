# Supply prices and scenario comparison

Implemented for local development on 20 October 2026. `energy_cost_monitor/pricing.py` evaluates detached [ledger intervals](accounting.md) without writing to the ledger or fetching prices. This is a comparison of electricity supply, excluding VAT. Network charges, taxes, levies, settlement credits and actual payment are outside this calculation.

## Scenario input

Use `parse_scenario(mapping)` to construct immutable scenarios. [Two synthetic offers](../examples/supply-scenarios.json) show the complete JSON schema. Their prices are invented and marked `reference`; they are not offers from actual suppliers.

Required top-level fields are `schema_version: 1`, a unique `id`, `currency: "EUR"`, `tax_basis: "excluding_vat"`, an IANA `timezone` and a nonempty `versions` array. Identifiers use lowercase letters, digits, underscores and hyphens, begin with a letter, and contain at most 64 characters. Unknown or omitted fields are rejected.

Each version has a unique `id`, `from`, `until`, `import`, `export` and `subscription`. Validity is half-open: the start is included, the end excluded. Timestamps must include an offset or `Z` and align to UTC quarter-hours. Versions and price periods are sorted on input; overlaps are rejected. Gaps and explicit expiry are allowed and produce unknown costs outside validity. A price period must fit entirely within its contract version. There is no indefinite fallback to the last known price.

`import` and `export` are arrays of price periods. Each period contains `from`, `until`, `value`, `unit`, `source` and `status`:

| Field | Meaning |
| --- | --- |
| `value` | Decimal string or integer; negative prices are allowed. `null` represents an unknown price. JSON floating-point values are rejected. |
| `unit` | `EUR/kWh` or `EUR/MWh`; the latter is divided by 1000 for calculation. |
| `source` | Nonempty provenance text, at most 1024 characters. A label or URL is evidence supplied by the caller, not automatically verified. |
| `status` | `confirmed`, `reference` or `unknown`. Only `unknown` accepts/requires `null`. |

Prices and monthly fees are limited to an absolute value of one billion, at most 12 decimal places and 48 input characters. These are numeric validation bounds, not recommended prices.

A fixed price can cover an entire contract version. Explicit hourly or quarter-hour periods can represent changing prices. An hourly price applies to its four UTC quarters; quarter-hour prices are never averaged. Missing prices may be represented by empty arrays, gaps or explicit unknown quotes. No provider-specific index, markup formula, market-data cache or network adapter is implemented.

`subscription` contains `value`, `unit: "EUR/month"`, `source` and `status` under the same rules, except that negative fees are rejected. A known absence of a fee must be explicit zero; unknown is not free. Discounts must already be reflected in the supplied nonnegative monthly amount.

## Evaluation

```python
import json
from pathlib import Path
from energy_cost_monitor.pricing import compare_scenarios, parse_scenario

scenarios = [
    parse_scenario(item)
    for item in json.loads(Path("examples/supply-scenarios.json").read_text())
]
# engine is an AccountingEngine with synthetic January 2026 measurements.
start, end = 1767225600, 1767312000
comparison = compare_scenarios(
    engine.intervals(start, end), scenarios,
    start=start, end=end, scope="import_export",
)
```

The window uses aligned UTC boundaries, is nonempty and is limited to 400 days, matching the ledger. Input may be unordered or omit buckets; duplicate, out-of-window and inconsistent intervals are rejected. Supply roles must have finite nonnegative energy of at most `1e15` kWh per bucket, with consistent coverage. Use scenarios returned by `parse_scenario`, not manually constructed dataclasses.

Scope is mandatory. `import_export` requires independently known import and export energy. `import_only` explicitly excludes export from the comparison; export results remain `None`, even if the ledger has no export source. Absence of a meter never establishes zero export. House, PV, battery, EV and heat-pump readings are not added to supply energy.

A role is priced only when the whole quarter-hour is covered and its price is known. Partial energy remains available in the ledger, but no full-quarter cost is inferred from it. Known zero energy or zero prices remain known. Even zero energy does not silently fill a missing price.

For each interval:

`net_cost = import_kwh × import_price − export_kwh × export_price + subscription_share`

In `import_only`, the export term is outside the selected scope. A negative import price reduces cost; a negative export price increases net cost. Price provenance and version ID accompany each interval. Missing data and reference inputs remain explicit in `reasons`.

## Monthly subscription policy

The configured monthly fee accrues evenly over local calendar days. Within each day, it accrues according to the elapsed fraction of that day's actual duration. A whole 23-hour or 25-hour day therefore receives the same monthly day share as an ordinary day. Month length, leap years, partial days and fee changes at version boundaries are respected.

This is a declared **comparison policy**, not an assertion about any supplier's contractual invoicing policy. Subscription accrues even when energy data is missing. The API does not round each interval; decimal calculations use a private precision-40 context, then summary money is rounded once to cents with `ROUND_HALF_UP`. Interval values remain unrounded. Independently rounded component subtotals can differ by a cent from the rounded net total. Savings are rounded from the unrounded difference, not from already rounded displayed totals.

Named timezones require an IANA timezone database. Python uses the operating system database or the `tzdata` package, often needed on Windows. If unavailable, parsing fails with `unknown_timezone`; it never substitutes the host's timezone. Tests used `Europe/Ljubljana` and `UTC` with available timezone data. Regional tariff/holiday rules are not part of this calendar calculation.

## Results and fair comparisons

Each `ScenarioResult` exposes:

- `import_subtotal`, `export_subtotal`, `subscription_subtotal`: known amounts for each component. Their coverage can differ.
- `known_net_subtotal`: only intervals where all components required by the scope are known. It need not equal the difference of the component subtotals.
- `total`: available only if every requested interval has all required components; otherwise `None`.
- Component coverage and joint `coverage`: fractions of expected buckets, including entirely missing ones.
- `confirmed`: all requested intervals are calculable and all used quotes are caller-labeled `confirmed`. This does not validate a contract, meter allocation or complete bill. Reference prices may produce numeric totals, but keep `confirmed=False`.

`Comparison.common_intervals` selects buckets calculable in **every** scenario. `common_totals` and `savings_vs_first` use that identical subset, including only the subscription shares in that subset. A positive difference means less cost than the first supplied scenario on the common evidence. No common evidence gives `None`, not a zero saving. Display `common_coverage` with any savings. Do not extrapolate or rank full-period offers from a partial comparison; omitted subscription shares may matter.

Synthetic daily example: 96 kWh imported and 48 kWh exported produce **EUR 16.90** for offer A and **EUR 12.68** for offer B, including their daily subscription shares. The common-scope difference is **EUR 4.22**. These tests establish arithmetic for invented inputs, not real savings.

## Limits and next step

The parser and comparison model do not persist profiles, amend measurement history, freeze reports or fetch/verify price sources. Repricing with newly supplied scenarios leaves stored energy unchanged. Currency conversion, VAT, network tariffs, holiday rules, credit carry-over and payment settlement remain future work.

Next: define a single-instance HA adapter with explicit counter sampling behavior, then test setup, options/reload, unload, task cancellation and recovery independently. The public package is still not installable.

## Slovenska navodila

Model primerja prevzem, oddajo in naročnino v EUR brez DDV. Cene imajo izrecno veljavnost, vir in status; primera ponudb sta izmišljena. Negativne cene so podprte. Naročnina se v primerjavi deli po lokalnih koledarskih dnevih.

Pri manjkajoči ceni ali nepopolni meritvi celotni znesek ostane neznan. Razliko ponudb vedno prikaži skupaj s skupno pokritostjo, saj se računa samo na istih uporabnih intervalih. `import_only` pomeni izrecno primerjavo samo prevzema in naročnine; ne dokazuje ničelne oddaje. To še ni celoten račun ali dejansko plačilo.
