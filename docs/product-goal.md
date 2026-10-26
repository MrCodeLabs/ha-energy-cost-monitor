# Product goal and completion criteria

Confirmed direction: 26 October 2026. These are requirements, not a claim that
every feature is already implemented or that a supported release is available.

## A reusable integration configured through Home Assistant

Help other households understand and compare energy costs without maintaining
custom code. Deliver one general integration installed and updated through HACS.
An ordinary user must be able to complete the supported workflows through settings
and guided forms, without editing Python, JavaScript, YAML or JSON, running migration
scripts, or installing household-specific patches. Advanced tools may remain
optional; they must not be prerequisites for normal installation or migration.

Users select their existing sensors, capabilities and units, configure tariffs,
validity dates, import/export terms, price-index basis and markups, regional bill
components, EV interpretation and study periods in the UI. Solar, batteries, EVs
and heat pumps remain optional. Device-specific identity, thresholds and contracts
must not be embedded in the shared code. Unsupported rules or missing inputs must
be explained rather than silently replaced with assumptions or zero costs.

The supported product scope includes supply comparisons, coverage/quality, EV
sessions and modes, study progress, regional billing and frozen reports. Completing
these workflows means implementing general configurable capabilities, not keeping
a separate private fork. Regional support must state its actual verified scope;
this goal does not imply support for every country or supplier.

## Privacy and distribution boundary

- Public repository: general code, configuration schemas/forms, documentation,
  sourced public rules and synthetic examples/tests.
- User's HA: entity selections, contract settings, profiles, measurements, study
  state, reports, migration mappings and any credentials, in private storage.
- No real household identifiers, private paths/topology, invoices, databases,
  logs or credentials in Git, release assets, screenshots or test fixtures.
- Updates preserve user settings and data outside the installed code directory.
  Incompatible storage changes need an explicit migration and recovery path.
- No private-data upload or telemetry is required for setup. Optional external
  price sources must explain what is sent and require an explicit configuration.

## Acceptance gates

- [ ] A fresh HACS installation can be configured with UI forms alone, including
  the dashboard/card, without manual file edits or a required JSON editor.
- [ ] A different user can configure a different set of synthetic sensors and
  contracts without changes to the repository or assistance from its author.
- [ ] Supported tariffs, export rules, EV behavior and study settings are editable
  with validation, units, effective dates and visible missing-data explanations.
- [ ] Guided legacy import previews mappings and unsupported fields, preserves
  originals, and tests both-store recovery without shell commands for the user.
- [ ] HACS update/restart retains settings, historical measurements and reports;
  recovery is documented and exercised on an isolated copy.
- [ ] Clean-install and migration results match the defined reference cases;
  known EV, study and regional-billing gaps are resolved before replacement claims.
- [ ] Public artifacts contain only reviewed general content and invented data.

The HACS custom-repository installation has been demonstrated in a lab. The
configuration-only experience, complete migration and workflow parity remain
unfinished. Existing JSON editors and offline converters are development aids,
not the final user experience. Default-catalog listing is a separate milestone.

## Slovenski povzetek

Cilj je integracija, ki tudi drugim olajša spremljanje stroškov energije:
namestitev in posodobitve prek HACS, nato vse nastavitve prek obrazcev v HA.
Uporabnik ne dopisuje kode, ne ureja JSON/YAML in ne potrebuje zasebnih popravkov.
Lastne senzorje, tarife, oddajo, EV in študijo nastavi lokalno; zasebni podatki
ostanejo v njegovem HA. Javni repo vsebuje samo splošno rešitev in izmišljene
primere. Dokaz dokončanosti je uspešna nastavitev in uporaba na čisti namestitvi
z drugačno konfiguracijo ter ohranitev podatkov po nadgradnji in obnovi.
