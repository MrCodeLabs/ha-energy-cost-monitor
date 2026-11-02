# New user guide

Updated 2 November 2026 · [Slovenščina](getting-started.sl.md) · [Project overview](../README.md)

## 1. Before you install

This is a development integration for a separate test HA, not an add-on. The
verified environment is HA Core 2026.10.2 with HACS 2.0.5; other versions are not
established by that test. You need an HA administrator, working HACS and existing
energy sensors. Follow the [official HACS setup](https://www.hacs.dev/docs/use/)
if HACS is not installed. Do not copy production credentials into a test instance.

Prepare cumulative household-consumption and grid-import counters, their actual
units and plausible power/freshness limits. Optional capabilities need their own
appropriate counters/signals. Power in kW is not cumulative energy in kWh.
You can start with sources only and add prices later. Prepare contract validity,
import/export prices, subscription and, if needed, agreed block powers and regional
rates privately. Blank prices mean unknown; zero means an actual zero charge.

**Do not install over an existing `energy_cost_monitor` component.** HACS replaces
that same component directory. Back up the test HA before installation; migrating
a production prototype is a separate procedure. Only one ECM entry is supported.

## 2. Download through HACS

1. Open HACS, then its top-right menu → **Custom repositories**.
2. Add `https://github.com/MrCodeLabs/ha-energy-cost-monitor`, type **Integration**.
3. Open **Energy Cost Monitor (development)** and download it. Record the commit
   shown by HACS; `532012e` is the revision verified on 2 November. A later `main`
   download may contain newer work, and an open PR is not included automatically.
4. Restart the test Home Assistant.
5. Open **Settings → Devices & services → Add integration → Energy Cost Monitor**.

This follows the [official custom-repository procedure](https://www.hacs.dev/docs/faq/custom_repositories/).
There is no stable release tag or default-catalog listing at this milestone.

## 3. Select sources and open the panel

Choose **Guided sensor setup** (Slovenian: **Voden izbor senzorjev**), select only
capabilities you have, and choose each source entity, unit, measurement type,
maximum report age and plausible power. Companion freshness signals are optional;
use one only if it reliably establishes the counter's freshness. Review and save.

For a minimal setup without solar, battery or export, the same counter may serve
house/import with identical settings. Otherwise provide appropriate separate
counters. An unavailable sensor does not validate its units.

The **Energy Cost Monitor** sidebar panel appears automatically for admins.
No dashboard resource or manual card YAML is required. Its tabs currently have
Slovenian labels; the steps below use those exact labels. JSON and manual Lovelace
setup are optional advanced paths, not prerequisites.

## 4. Configure the functions you need

| Tab | What to do |
| --- | --- |
| **Cene** (prices) | Name the profile, add an offer and contract version, enter validity, subscription and import/export price periods. Select units, record sources and confirm only verified prices. Choose **Shrani cenovni profil**. |
| **Profili** (profiles) | Inspect saved versions or activate a previous version. Changes create new versions; frozen reports retain their original assumptions. The advanced JSON editor is optional. |
| **EV in obračun** (EV and billing) | Optionally enable counter-level EV calculation and enter gap/power/tolerance thresholds. Under regional settings, add effective dates, block rates, agreed powers, levies, VAT and excess-power mode. Save with **Shrani EV in obračun**. |
| **Študija** (study) | Choose timezone, months, warm-up, coverage and daily-check settings; select **Začni uvajanje študije**. The required daily household reference is selected in source settings. |
| **Poročila** (reports) | Choose a view window, then **Zamrzni prikazano obdobje**. Open/download the frozen HTML or CSV report. |

Price timestamps need an offset, for example `2026-01-01T00:00:00+01:00`; the end
is exclusive. Use the correct offset for the date. Regional dates are entered as
dates. Connection power is **not** agreed billing power for tariff blocks.

For an invented practice offer, use EUR/kWh, import `0.15` and subscription `2`
EUR/month excluding VAT, with explicit validity dates. Label the source
“Synthetic example” and leave confirmation unchecked. These are not tariffs or
recommended household settings; replace them before interpreting real results.

The optional **Referenčni indeks Energy-Charts + pribitek** price mode replaces
entered import prices within contract validity. Select the zone and markup in the
form. It sends only zone/date requests, not measurements or profiles; the provider
sees the requesting network address. Fetching/backfill is gradual and not an
instant supplier feed. Index results remain reference values.

EV modes are observed, not commanded. Study warm-up ends only after its quality
gates pass; a required missing daily reference keeps it waiting. Live testing
verified warm-up and persistence; monthly/final reporting was tested with simulated
time. Regional references cover Slovenia **2026 only**. Credit, payouts and a final
amount payable are unfinished. HTML retains regional evidence; CSV currently
exports energy/supply rows, not an equivalent full regional bill.

## 5. Optional legacy history import

Skip this for a new installation. **Uvoz zgodovine** accepts a supported legacy
Energy Cost Monitor SQLite copy, not an arbitrary HA recorder database or CSV.
Use a consistent backup, never a live database file copied during writes.

1. Back up both current ECM stores and HA configuration.
2. Select the legacy SQLite copy in the import form and review its preview.
3. Map every requested role, select the source profile and the exclusive end date
   for comparing old prices. Decide whether to activate the converted profile.
4. Confirm the reviewed mapping, then choose **Uvozi preverjeno zgodovino**.
5. Check the imported counts, backup identifier, profiles and archived reports.

The upload goes to your HA. Original rows are retained; overlap with native
collection, unsupported or already-imported history is refused. Both stores get a
pre-import backup. A staged upload can be resumed/discarded without changing your
original file. Old study and regional settings are not activated automatically;
review/configure them separately. This is not full HA recovery. See
[migration details and limits](application-migration.md).

## 6. Check the result

- Check the collection-quality sensor and the panel's latest sample time.
- Allow the counters to report and a quarter-hour interval to finish. Initial,
  stale or incomplete measurements may correctly show **neznano** (unknown).
- Reopen saved settings and check active profile, periods, units and confirmation.
- Freeze a test report and verify it remains available after a test restart.
- Distinguish a known subtotal from a complete total. Neither establishes the
  supplier's payable amount. Do not mark unverified inputs confirmed to hide gaps.

## 7. Updates, backups and removal

Before updating, record the installed commit and take a consistent HA backup with
configuration and **both** private files: `.storage/energy_cost_monitor.sqlite3`
and `.storage/energy_cost_monitor_application.sqlite3`. For filesystem copies,
stop the integration/HA first. The old meter-only recovery ZIP omits the application
store. Export useful reports too; exports are not a complete backup.

Update through HACS, restart HA, then repeat the checks above and verify that
previous measurements, profiles and reports remain. Avoid automatic updates for
this development package. To roll back, stop collection, retain the current stores
including new measurements, and restore a compatible code/configuration/paired
store backup. An older code version may not read a newer schema. Never delete a
database to bypass that check; full HAOS restore has not been established here.

To stop using ECM, disable its entry in Devices & services. For removal, preserve
the backup, remove the entry, then remove the package through HACS and restart.
Removing the entry retains stored history; removing code is not a data purge or a
migration back to a legacy app. Source identity changes after collection require
a migration that is not provided by the reconfiguration form.

## Troubleshooting and feedback

| Symptom | Check |
| --- | --- |
| Integration/panel missing | Confirm HACS download, restart, add the integration, use an admin account and reload the browser. |
| Unknown totals | Sensor freshness/units, completed intervals, coverage, price dates and missing/unconfirmed rates. |
| Study stays in warm-up | Coverage and required daily-reference quality; waiting can be the correct result. |
| Reconfiguration/import refused | Read identity/overlap restrictions; retain data and correct the mapping instead of deleting stores. |
| Form rejected | Check numbers, units, timestamp offsets, validity and overlapping periods. |

Report a [sanitized issue](https://github.com/MrCodeLabs/ha-energy-cost-monitor/issues)
with HA/HACS versions, commit, steps and expected/actual behavior. Use invented
examples; omit personal data, tokens, private logs, invoices and databases.
[Acceptance evidence](acceptance-2026-11-02.md) and [roadmap](../ROADMAP.md) define
the current limits. Historical technical notes are not the first-install guide.
