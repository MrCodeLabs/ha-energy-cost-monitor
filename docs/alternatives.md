# Existing solutions and project rationale

## Guided reconfiguration follow-up — 28 October 2026

The same-day repository, issue/PR and separate frontend review below remains the
baseline. Re-read Dynamic Energy Cost and Powercalc config-flow implementations
and official [HA reconfiguration guidance](https://contributors.home-assistant.io/core/integrations/reauth-reconfigure/).
The gap is editing this project's source mapping while preserving its immutable
ledger identity and existing entry lifecycle, not a generic cost-sensor feature.
No upstream implementation was copied. Browser/mobile verification and versioned
source migrations remain separate gates.

## Guided setup follow-up — 28 October 2026

Reopened Dynamic Energy Cost and Powercalc repository/docs, config-flow source,
issue/PR pages and the separate MFFR Profit Tracker frontend before this change.
These remain relevant maintained alternatives for cost sensors and balancing-reserve
reporting. Web issue/PR views have differing cache dates, so no fresh queue counts
are asserted. The concrete gap is a guided entity/unit/capability mapping into this
project's existing ledger, without required JSON. Existing sensor cost work still
belongs upstream; this flow imports no upstream code or frontend.
Reviewed the official [HA flow steps](https://contributors.home-assistant.io/core/integrations/flow-steps/)
and upstream [Dynamic Energy Cost config flow](https://github.com/martinarva/dynamic_energy_cost/blob/main/custom_components/dynamic_energy_cost/config_flow.py)
and [Powercalc config flow](https://github.com/bramstroker/homeassistant-powercalc/blob/master/custom_components/powercalc/config_flow.py).

## Legacy conversion follow-up — 26 October 2026

Reopened the Dynamic Energy Cost and Powercalc repositories, READMEs, sensor/cost
source, issue and PR lists, and the same author's MFFR Profit Tracker frontend.
Both cost integrations remain maintained sensor-oriented alternatives; the MFFR
frontend serves balancing-reserve reporting. Issue/PR web views may be cached, so
this is not proof of their live queue state. The 25 October review below remains
the detailed comparison baseline. The specific gap here is compatibility with
this project's owner-authorized legacy database/profile/report format and paired
recovery, not a new generic cost sensor. No upstream code is copied.

Sources: [Dynamic Energy Cost](https://github.com/martinarva/dynamic_energy_cost),
[Powercalc cost source](https://github.com/bramstroker/homeassistant-powercalc/blob/master/custom_components/powercalc/sensors/cost.py),
[MFFR frontend](https://github.com/martinarva/MFFR-Profit-Tracker).

Review date: 18 October 2026. This is a scoped comparison, not an exhaustive survey or a claim that no other solution exists. No third-party code has been copied into this repository.

## Dynamic Energy Cost

[Repository](https://github.com/martinarva/dynamic_energy_cost) · [sensor implementation](https://github.com/martinarva/dynamic_energy_cost/blob/main/custom_components/dynamic_energy_cost/sensor.py)

The reviewed manifest reports 1.2.4. GitHub metadata reports a non-archived MIT-licensed project. It supports cost sensors from price and energy/power inputs, configurable intervals, unit conversion and a manual-reset use case. Its README explicitly scopes full contract/billing logic, fixed charges, export deductions and alternative-contract comparisons outside the integration.

Relevant discussions include [separate import/export prices #243](https://github.com/martinarva/dynamic_energy_cost/issues/243), [session entity #235](https://github.com/martinarva/dynamic_energy_cost/issues/235), [network costs #223](https://github.com/martinarva/dynamic_energy_cost/issues/223), and [negative prices/energy delivery PR #31](https://github.com/martinarva/dynamic_energy_cost/pull/31). Their presence is not evidence that a feature is missing today; re-check current code and the discussion before implementing overlapping work. A search of the author's public repositories found no clearly dedicated companion cost dashboard; this is a limited search, not proof of absence.

Decision: use or contribute here for basic cost-sensor behavior. The proposed Energy Cost Monitor scope is broader contract comparison, quality evidence and report snapshots. Do not describe negative prices or interval sensors as novel features of this project.

## Powercalc

[Repository](https://github.com/bramstroker/homeassistant-powercalc) · [cost documentation](https://docs.powercalc.nl/sensor-types/cost-sensor/) · [cost implementation](https://github.com/bramstroker/homeassistant-powercalc/blob/master/custom_components/powercalc/sensors/cost.py)

GitHub metadata reports a non-archived MIT-licensed project. Cost sensors can use an existing energy sensor with fixed or sensor-based prices. The reviewed code includes unit conversion and price modifiers. This is a relevant existing solution for appliance and energy cost tracking.

The follow-up review on 18 October 2026 covered cost-related issues and PRs, including merged [price modifiers #4262](https://github.com/bramstroker/homeassistant-powercalc/pull/4262), [standalone cost flow #4265](https://github.com/bramstroker/homeassistant-powercalc/pull/4265) and [energy-unit conversion #4269](https://github.com/bramstroker/homeassistant-powercalc/pull/4269). These are existing capabilities, not gaps for this project. [Price-selector issue #4422](https://github.com/bramstroker/homeassistant-powercalc/issues/4422) is closed as completed; [PV/battery mixed-price request #4298](https://github.com/bramstroker/homeassistant-powercalc/issues/4298) is closed as not planned. Neither status alone proves present behavior. The discussion in [collaboration #2904](https://github.com/bramstroker/homeassistant-powercalc/issues/2904) now links Powercalc's own cost support, so the original request is not evidence of a missing basic cost sensor.

The author's [Powercalc Library Viewer](https://github.com/bramstroker/powercalc-library-ui) is a profile-library and analytics site. [Powercalc Measure](https://github.com/bramstroker/powercalc-measure-app) provides a UI for measuring device power profiles. Their READMEs do not describe the proposed contract-comparison/report-snapshot workflow.

## Follow-up evidence and implementation decision — 18 October 2026

GitHub repository metadata reports both primary projects as non-archived. Default-branch heads observed through the API were Dynamic Energy Cost [`53e2890`](https://github.com/martinarva/dynamic_energy_cost/commit/53e28904002960fe2f73c70b33dc58ac3cfed292) (6 September 2026) and Powercalc [`f9c6bbf`](https://github.com/bramstroker/homeassistant-powercalc/commit/f9c6bbf97ec20754591ed48b4d469964f0ede967) (18 October 2026). Activity and archive status do not guarantee future maintenance or compatibility.

Re-read Dynamic Energy Cost's README, manifest (1.2.4), config flow and sensor code, and Powercalc's cost documentation and `sensors/cost.py` (blob `acc80c44486e56e0f07c214ce8814349c390e16d`). Dynamic Energy Cost already validates consumption-source selection and converts units. Its README explicitly leaves full billing and alternative-contract comparisons outside its scope. Powercalc already accepts existing energy meters and dynamic or fixed prices. No code from either project is imported.

The scoped issue/PR search included current import/export discussion [#243](https://github.com/martinarva/dynamic_energy_cost/issues/243), calibration report [#246](https://github.com/martinarva/dynamic_energy_cost/issues/246), reset PR [#132](https://github.com/martinarva/dynamic_energy_cost/pull/132) and configuration PR [#194](https://github.com/martinarva/dynamic_energy_cost/pull/194). Reports and historical patches are inputs to review, not claims of an unresolved defect in the current source.

Searching the authors' public repository names/descriptions also found [MFFR Profit Tracker](https://github.com/martinarva/MFFR-Profit-Tracker): its README describes a React frontend and backend for balancing-reserve battery revenue, rather than a companion contract-cost dashboard. This qualifies the earlier limited frontend search. Searches covered `user:martinarva` and `user:bramstroker fork:false`, plus the linked frontend READMEs; they are not an exhaustive audit of every repository or frontend file.

Decision: proceed with a small, HA-independent source-configuration boundary for this project's planned quality-aware accounting and frozen scenario reports. Its concrete need is to describe independent meters, optional solar/battery/EV/heat-pump capabilities, freshness and plausibility thresholds without household defaults. Basic unit conversion and cost-sensor improvements still belong upstream where applicable. This step does not implement billing, a HA adapter or a card, and does not claim that the complete planned workflow is already available.

## Decision for this repository

### HA adapter follow-up — 23 October 2026

Refreshed the primary repositories, Dynamic Energy Cost's README and integration
setup/reload implementation, Powercalc's cost documentation and `sensors/cost.py`,
the import/export request [#243](https://github.com/martinarva/dynamic_energy_cost/issues/243)
(open), and the standalone cost flow [PR #4265](https://github.com/bramstroker/homeassistant-powercalc/pull/4265)
(merged). Both repositories remain non-archived. Observed default heads were
Dynamic Energy Cost [`53e2890`](https://github.com/martinarva/dynamic_energy_cost/commit/53e28904002960fe2f73c70b33dc58ac3cfed292)
and Powercalc [`d2d15cb`](https://github.com/bramstroker/homeassistant-powercalc/commit/d2d15cb9c5db285557369853ccf2ba7e669b67e6).
Re-read the related [MFFR Profit Tracker README](https://github.com/martinarva/MFFR-Profit-Tracker):
its React frontend remains described around balancing-reserve operation/revenue.
This refresh uses the earlier author/frontend survey and does not claim an
exhaustive new search of all projects.

Decision: retain upstream tools for ordinary energy-cost sensors. This adapter's
specific purpose is to feed the existing independent coverage ledger and detached
supply comparisons, preserve unknown intervals and storage identity, and manage
their single-writer lifecycle. Neither upstream implementation was copied. No
new dashboard is introduced. The distinction remains a development objective,
not a claim of complete billing or reporting support.

HA API review used [config-entry lifecycle documentation](https://developers.home-assistant.io/docs/config_entries_index/),
[options-flow documentation](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/),
the [report timestamp announcement](https://developers.home-assistant.io/blog/2024/03/20/state_reported_timestamp/)
and [Core 2026.10.2 source](https://github.com/home-assistant/core/tree/2026.10.2).
The reviewed release uses `probatio` schemas. Report timestamps describe state
reports to HA, which cannot prove the physical measurement time of a cached or
rounded source. Actual HA execution and hassfest are still pending.

### Meter-accounting follow-up — 20 October 2026

Rechecked Dynamic Energy Cost's default head: it remains `53e28904002960fe2f73c70b33dc58ac3cfed292`. Re-read Powercalc's current cost accumulation, source-reset and missing-price handling (`sensors/cost.py`, blob `148d58d733862b821bdd74bec0d2782ef5744703`); its cost source has changed since the earlier review, while the reviewed basic-sensor boundary still applies. The [PV/battery request #4298](https://github.com/bramstroker/homeassistant-powercalc/issues/4298) remains closed, last updated 3 September 2026. The dated issue/PR/frontend review above remains the comparison baseline; no new frontend implementation is being proposed here.

The current extraction adds an independent ledger of cumulative energy, covered time and unallocated gaps. Collection does not depend on price availability. It does not duplicate a price-times-energy sensor, and does not yet implement the planned contract comparison. Basic cost-sensor changes should still go to the relevant upstream project.

### Supply-scenario follow-up — 20 October 2026

Using the same day's scoped upstream review above, the next local step implements detached, versioned supply-scenario comparison with explicit validity, monthly subscription allocation and comparisons on common covered intervals. This addresses the previously documented alternative-contract workflow. It adds no HA integration or frontend and imports no upstream implementation. Basic cost sensors remain an upstream use case; a full bill model and frozen reports remain unimplemented here.

Create a separate project home and document extraction of the existing privately developed accounting/reporting workflow. Do not fork or duplicate the basic cost-sensor implementations above. Code extraction will require another scoped comparison before integration/frontend changes.

The initial published baseline was documentation only. Current local development adds the source boundary and cumulative-meter ledger described above. The intended distinguishing combination remains versioned supply scenarios, import/export accounting, regional bill components, explicit coverage/uncertainty and frozen comparison reports. The first installable implementation must demonstrate that combination before advertising it as supported.

## HACS milestones

### History preservation follow-up — 23 October 2026

Default heads were rechecked: Dynamic Energy Cost remains `53e2890` and Powercalc
remains `d2d15cb9`. The same-day source/docs, issue/PR and related-frontend review
above remains the comparison baseline. Offline preservation of this project's
legacy records and its single-writer backup lifecycle are project-specific gaps;
no upstream implementation is imported. Backup hooks follow the
[official HA backup platform](https://developers.home-assistant.io/docs/core/platform/backup/).

Public GitHub hosting, custom-repository installation and default-catalog inclusion are separate milestones. Follow the current [general requirements](https://www.hacs.dev/docs/publish/start/), [integration requirements](https://www.hacs.dev/docs/publish/integration/) and [catalog process](https://www.hacs.dev/docs/publish/include/). No successful HACS/hassfest validation or catalog acceptance is claimed at project setup.

### Recovery verification follow-up — 23 October 2026

The same-day upstream source/docs, issue/PR and frontend comparison above remains the baseline. This offline-only change verifies preservation of this project's own legacy rows and mapped intervals; it does not add a cost sensor or frontend. No upstream code is imported. The official HA backup documentation was re-opened; the recovery ZIP does not replace HA backup/restore or claim full application rollback.

### Restore follow-up — 24 October 2026

Rechecked default source heads through GitHub: Dynamic Energy Cost remains `53e28904002960fe2f73c70b33dc58ac3cfed292`, Powercalc remains `d2d15cb9c5db285557369853ccf2ba7e669b67e6`. The previous source/docs and issue/PR/frontend review remains the scoped baseline, not a claim that no new issues exist. This offline restore step serves this project's own migration format; it adds no sensor or frontend and imports no upstream code.

Reconciliation follow-up, 24 October 2026: the same-day source-head check and existing source/docs, issue/PR/frontend comparison remain the scoped baseline. This change implements compatibility with the owner-authorized legacy format, not another general cost sensor. No upstream code or frontend is imported.


### Application/card follow-up — 25 October 2026

Rechecked public repositories, current source/docs and open issues before this
integration/frontend extension. Dynamic Energy Cost remains at `53e2890` (active);
recent issues #245–247 concern documentation, calibration and source attributes.
Powercalc is active at `948016c`; current `sensors/cost.py` still serves source
energy/cost accumulation and handles price units/surcharges. Recent #5064/#5065
are device-profile submissions. The previously reviewed PV/battery and standalone
cost requests remain part of the comparison, not newly verified capabilities.
Re-read the author's [MFFR Profit Tracker](https://github.com/martinarva/MFFR-Profit-Tracker)
README: its React UI concerns balancing-reserve profit, not this project's paired
ledger/profile snapshots and conservative EV-session coverage.

The concrete gap here is a UI/API over this project's existing independent ledger,
versioned alternative contracts, preserved missing coverage, source-price provenance
and immutable reports. This is a scoped comparison, not an exhaustive catalog
survey. Basic cost-sensor improvements still belong upstream. No upstream source
or frontend was copied. Reviewed official [HA custom-card documentation](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/),
[REST view documentation](https://developers.home-assistant.io/docs/api/rest/),
Core 2026.10.2 authentication/HTTP APIs and the frontend authenticated fetch methods.
Price parsing follows the [Energy-Charts v2 OpenAPI schema](https://api.energy-charts.info/openapi.json);
its reference index is not asserted to equal a supplier billing index.


### HA scheduler correction — 26 October 2026

The 25 October upstream feature/source/frontend survey remains the scoped baseline.
This is a correction to our own scheduled callback, not a new integration/UI feature.
Reviewed [Core 2026.10.2 HassJob dispatch](https://github.com/home-assistant/core/blob/2026.10.2/homeassistant/core.py):
plain synchronous targets run in the executor; `@callback` marks event-loop work.
The real scheduler regression is now exercised by the isolated HA lab.

### Configuration-only continuation — 28 October 2026

The same-day review of Dynamic Energy Cost, Powercalc and the author's separate
MFFR Profit Tracker remains the scoped comparison for the initial wizard and this
continuation. The gap is configuration and migration over this project's paired
ledger/application stores, observed EV modes and immutable study reports. No
upstream implementation was copied. Reviewed Core 2026.10.2 frontend/panel_custom
registration and the official [file upload implementation](https://github.com/home-assistant/core/blob/2026.10.2/homeassistant/components/file_upload/__init__.py).
Uploads use HA's authenticated file-upload facility and admin-only import endpoints.
