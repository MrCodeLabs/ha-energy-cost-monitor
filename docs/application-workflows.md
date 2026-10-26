# Application workflows — local development, 25 October 2026

This branch connects live EV sessions, optional reference-price collection,
versioned profiles, frozen reports and an authenticated API/card. It is not a
release or a complete replacement for the legacy application. No production
configuration or household data was used in development.

## Try in an isolated HA installation

Install this development integration using the [lab instructions](lab-validation.md).
Configure source entities through the existing integration flow. As an HA admin,
add a dashboard resource of type **JavaScript module**:

`/energy_cost_monitor/energy-cost-monitor-card.js`

Then add a manual card:

```yaml
type: custom:energy-cost-monitor-card
title: Energy Cost Monitor
```

The resource is served by the loaded integration; restart HA after updating the
card file. Registration is manual, not an automatic Lovelace configuration change.
The card currently uses Slovenian labels and requires an administrator account.
It refreshes every 30 seconds and supports rolling 1/7/30-day UTC windows ending
at the last completed quarter hour. Session observations may extend to now.
Displayed timestamps use the browser's local timezone. Longer windows and full
calendar billing periods are not provided by this first UI.

## Profiles and prices

Use **Profili → Nov enostaven cenovni profil** to enter a name, validity dates,
import/export prices in EUR/kWh and a monthly subscription in EUR. Dates in this
simple form are UTC boundaries, with an exclusive end. Empty amounts mean
unknown; enter `0` explicitly for a zero charge. Prepare and then save the profile.
The advanced editor supports multiple scenarios, contract periods and sources.
[application-profile.json](../examples/application-profile.json) is an invented
example; replace its values and validity before use. A saved edit is an immutable
version, identified by the SHA-256 of canonical JSON. Older versions can be
activated again. Refresh is suspended while editing the advanced draft.

To opt into public reference prices, add an `indexed_import` binding, for example:

```json
{"offer-a": {"zone": "SI", "markup_eur_kwh": "0.02"}}
```

This replaces the bound scenario's import prices within its validity windows;
export and subscription still come from the profile. Empty `{}` disables all
external price requests. Supported zones: SI, AT, DE-LU, HR, IT-North, HU.
`session_charging_kw` is an optional profile number (default 0.1 kW) controlling
the sampled charging/pause classification. It does not control the charger.

The integration calls the fixed public [Energy-Charts v2 price API](https://api.energy-charts.info/)
with zone/date only; it sends no measurements, entity IDs or profiles. The provider
can see the requesting network address. One request per hour rotates through today,
tomorrow and the previous seven dates for each configured zone. A complete sweep
takes nine hours per zone; backfill is gradual, resets its cursor after restart,
and does not guarantee today's prices are already available. The date label is
chosen from UTC; the provider interprets it in the zone's local calendar.
HTTP errors retry on the next slot; a numeric Retry-After can delay up to 24 hours.
Responses are bounded to 2 MB and 400 entries, redirects refused, timeouts 20 s.
Price failure does not stop the independent measurement collector.

Only explicit 15/60-minute periods and EUR/MWh are accepted. Hourly prices expand
to four quarters, negative prices remain valid, gaps remain unknown, and null
retries cannot erase known quotes. Prices are converted using Decimal. Raw source
responses and attribution are retained privately; provider license/source details
appear in frozen evidence and exports. The index remains **reference**, not a
confirmed supplier billing formula. Historical cache corrections never rewrite a
previously frozen report.

## Sessions and reports

Sessions use configured connection/power signals and the existing meter ledger.
Charging and pause durations are sampled estimates. Missing connection data does
not imply disconnection. A still-open session retains a null end; sessions that
started before the selected window are partial. Only complete quarter-hour
allocations contained within a session contribute its energy. Edge intervals and
gaps remain explicit; without covered energy the total is unknown, not zero.
There is no mode classification, signal integration or push event stream yet.

**Poročila → Zamrzni prikazano obdobje** stores a snapshot of interval data,
sessions, the selected profile version, supply calculations and price provenance.
HTML contains summary totals plus full evidence; CSV contains energy and supply
rows, with source attribution. Missing full coverage gives an unknown full total
and a separate known subtotal. Reports are supply-only, excluding VAT, network
charges and levies. A complete utility bill and golden invoice validation remain
open. Repeated freezes create distinct captures; there is no automatic retention
or deletion. API lists show the latest 100 profiles/reports; saved report IDs remain
readable beyond this list. Retain exported IDs if using more than 100 reports.

## API and storage boundary

All `/api/energy_cost_monitor/*` actions require HA authentication **and admin**.
The public JavaScript route contains code only. Tokens stay in HA's existing
authenticated client and are never embedded in card configuration.

| Method/action | Purpose |
| --- | --- |
| GET `view?start=…&end=…` | UTC epoch seconds, aligned quarters, at most 31 days |
| GET/POST `profiles` | Read versions / save complete profile, or `{"activate":"id"}` |
| GET/POST `reports` | List captures / freeze `{"start":…, "end":…}` |
| GET `report?id=…&format=json\|html\|csv` | Retrieve one immutable capture |
| GET `market` | Cache freshness, generic fetch error, next attempt |

Requests are bounded to 256 KB and views to 250,000 samples; shorter windows are
required beyond that limit. Private responses are no-store. HTML downloads have a
sandbox CSP and escape user/source text. No SQLite download endpoint exists.
Invalid or temporarily unavailable requests return generic errors without local
paths. APIs are development contracts, not compatibility with the old API.

Measurements remain in `.storage/energy_cost_monitor.sqlite3`. New profiles,
price payloads/cache and reports are in the separate schema-1
`.storage/energy_cost_monitor_application.sqlite3`. Never put either file in Git
or HA's public `www` directory. All writes use executor work and transactions;
shutdown drains it. HA pre-backup blocks new application work and drains both
writers; post-backup resumes collection. A cancelled backup also resumes it.

**Back up and restore both databases together with the integration configuration.**
Use HA backup or stop the integration/process before making a filesystem copy.
Keep the previous files in a separate recovery directory; restore only into vacant
paths with matching source configuration. The laboratory verifies paired SQLite
snapshots and process restart, not an HAOS full-machine restore.
The existing meter `recovery-bundle`/`restore-bundle` CLI packages only the meter
ledger and legacy export: it does **not** contain the new application store.
Legacy profiles/reports remain archived by migration, not automatically converted
to this new UI. New application profiles/reports also do not become legacy rows
through reconciliation. Export and preserve them separately during a rollback.

## Verification and next gates

Tests cover immutable versions, price gaps/negative values/DST, report stability,
HTML escaping, CSV costs, live session endpoints, admin checks, price outages,
reload and backup cancellation. The real HA lab exercises HTTP 401/403/admin
success, profile writes, public code serving, five creation/restart/restore phases
and restoration of a frozen report from the second database. Card tests use a
minimal DOM double: refresh, draft retention/discard, literal text, stale requests
after disconnect and the simple profile form. They are not browser visual tests.

Next: real Lovelace browser/mobile UX and downloads; conversion of legacy
profiles/reports; mode/event and signal features used by the old UI; dated regional
bill components and golden invoice fixtures; independent user configuration and
full HA backup/restore. Production replacement and a public HACS beta remain
separate gated steps.

## Slovenska uporaba in omejitve

Kartico dodaj le v ločeni testni HA: zgornji naslov kot JavaScript modul in tip
`custom:energy-cost-monitor-card`. Potrebuješ skrbniški račun. Na zavihku Profili
pripravi in shrani svoj cenovni profil; prazno polje pomeni neznano, ne nič.
Za cenovni zajem izrecno nastavi `indexed_import`. Meritve ostanejo neodvisne od
dosegljivosti cen. Poročilo shrani tedanje podatke in predpostavke, vendar še ni
celoten račun. Pri kopiranju in povratku ohrani **obe zbirki**; stari obnovitveni
ZIP nove aplikacijske zbirke ne vključuje. Podatkov, baz in lastnih profilov ne
objavljaj. Produkcija se s tem razvojnim korakom ne spreminja.
