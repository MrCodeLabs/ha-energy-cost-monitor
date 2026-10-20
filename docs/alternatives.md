# Existing solutions and project rationale

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

### Meter-accounting follow-up — 20 October 2026

Rechecked Dynamic Energy Cost's default head: it remains `53e28904002960fe2f73c70b33dc58ac3cfed292`. Re-read Powercalc's current cost accumulation, source-reset and missing-price handling (`sensors/cost.py`, blob `148d58d733862b821bdd74bec0d2782ef5744703`); its cost source has changed since the earlier review, while the reviewed basic-sensor boundary still applies. The [PV/battery request #4298](https://github.com/bramstroker/homeassistant-powercalc/issues/4298) remains closed, last updated 3 September 2026. The dated issue/PR/frontend review above remains the comparison baseline; no new frontend implementation is being proposed here.

The current extraction adds an independent ledger of cumulative energy, covered time and unallocated gaps. Collection does not depend on price availability. It does not duplicate a price-times-energy sensor, and does not yet implement the planned contract comparison. Basic cost-sensor changes should still go to the relevant upstream project.

### Supply-scenario follow-up — 20 October 2026

Using the same day's scoped upstream review above, the next local step implements detached, versioned supply-scenario comparison with explicit validity, monthly subscription allocation and comparisons on common covered intervals. This addresses the previously documented alternative-contract workflow. It adds no HA integration or frontend and imports no upstream implementation. Basic cost sensors remain an upstream use case; a full bill model and frozen reports remain unimplemented here.

Create a separate project home and document extraction of the existing privately developed accounting/reporting workflow. Do not fork or duplicate the basic cost-sensor implementations above. Code extraction will require another scoped comparison before integration/frontend changes.

The initial published baseline was documentation only. Current local development adds the source boundary and cumulative-meter ledger described above. The intended distinguishing combination remains versioned supply scenarios, import/export accounting, regional bill components, explicit coverage/uncertainty and frozen comparison reports. The first installable implementation must demonstrate that combination before advertising it as supported.

## HACS milestones

Public GitHub hosting, custom-repository installation and default-catalog inclusion are separate milestones. Follow the current [general requirements](https://www.hacs.dev/docs/publish/start/), [integration requirements](https://www.hacs.dev/docs/publish/integration/) and [catalog process](https://www.hacs.dev/docs/publish/include/). No successful HACS/hassfest validation or catalog acceptance is claimed at project setup.
