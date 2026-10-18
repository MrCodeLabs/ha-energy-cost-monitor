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

The current review does not establish the complete issue/PR landscape or all author-maintained frontend projects. Before changing overlapping functionality, extend that review rather than assuming this project fills a gap.

## Decision for this repository

Create a separate project home and document extraction of the existing privately developed accounting/reporting workflow. Do not fork or duplicate the basic cost-sensor implementations above. Code extraction will require another scoped comparison before integration/frontend changes.

The first public project is documentation only. Its intended distinguishing combination is versioned supply scenarios, import/export accounting, regional bill components, explicit coverage/uncertainty and frozen comparison reports. The first implementation must demonstrate that combination before advertising it as supported.

## HACS milestones

Public GitHub hosting, custom-repository installation and default-catalog inclusion are separate milestones. Follow the current [general requirements](https://www.hacs.dev/docs/publish/start/), [integration requirements](https://www.hacs.dev/docs/publish/integration/) and [catalog process](https://www.hacs.dev/docs/publish/include/). No successful HACS/hassfest validation or catalog acceptance is claimed at project setup.
