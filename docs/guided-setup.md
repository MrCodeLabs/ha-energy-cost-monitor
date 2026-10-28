# Guided source setup — local development, 28 October 2026

New installations can choose **Guided sensor setup** instead of entering source
JSON. This is one step toward the [configuration-only product goal](product-goal.md),
not completion of the full product or a supported production release.

1. Add Energy Cost Monitor in HA Devices & services and choose guided setup.
2. Select optional measurements. Household consumption and grid import are always
   required; selecting a solar/battery/EV signal adds its required energy counters.
   Do not select capabilities without those counters.
3. For each source, select an entity, measurement type/unit, maximum report age
   and (for energy) maximum plausible power. Cumulative counters and daily
   heat-pump estimates are distinct choices. Units are checked against current
   HA attributes when available; an unavailable sensor is not proof of correct units.
4. Optionally select companion signals that reliably prove an energy counter's
   freshness. Wrong dependencies can accept stale energy; use them deliberately.
5. Review mappings and save, or restart selection. The same validated core models
   and existing-store identity checks apply. No database is created by the form.

A single sensor may serve house/import only with identical settings and without
solar, battery or export. Configure separate counters otherwise. Limits and
freshness values are user settings, not device-control commands. Saved entity
IDs and settings stay in private HA configuration; no household defaults ship.

Advanced JSON import remains optional. Reconfiguration of an existing entry still
uses the previous advanced form and cannot change stored ledger identity without
migration. The wizard does not yet cover tariff/regional forms, EV modes, study,
guided history import or card installation. It does not fetch prices or alter
profiles. These remain explicit acceptance gates.

Validation covers a minimal shared-counter setup, optional capability dependencies,
daily estimates, unit mismatch, conflicting aliases and restart of the draft.
The real HA lab creates fresh entries through the guided flow and checks collection,
restart and restore. This is a real HA flow test, not a desktop/mobile visual test
or an independent user's HACS installation of this unpublished branch.

## Slovenščina

V HA izberi dodajanje integracije in **Voden izbor senzorjev**. Izberi dodatne vire,
nato za vsak vir senzor, dejansko enoto, vrsto meritve, svežino in močnostno mejo.
Preglej preslikavo ter shrani. JSON za začetno nastavitev virov ni potreben.
Pri minimalni hiši lahko isti števec uporabiš za house/import z enakimi omejitvami;
pri sončni elektrarni, bateriji ali oddaji sta potrebna ustrezna ločena vira.

To še ni dokončana nastavitev celotne aplikacije samo z obrazci. Regionalni račun,
študija, EV razlike, voden uvoz, nastavitev kartice in sprememba obstoječih virov
ostajajo odprti. Uporabljaj v ločenem laboratoriju; zasebne nastavitve ne sodijo v Git.
