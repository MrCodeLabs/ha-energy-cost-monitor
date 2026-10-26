# HACS development package

## Interactive installation verified — 26 October 2026

[PR #5](https://github.com/MrCodeLabs/ha-energy-cost-monitor/pull/5) merged as
`a9c9b5abc96c7296493318450bcba6815300336d`. All 11 PR checks passed
([run](https://github.com/MrCodeLabs/ha-energy-cost-monitor/actions/runs/40362927438));
the resulting main CI also passed ([run](https://github.com/MrCodeLabs/ha-energy-cost-monitor/actions/runs/40363297381)).

A fresh, isolated HA 2026.10.2 installation used official HACS 2.0.5. The operator
created a separate test account and authorized HACS through the normal GitHub
device flow. Through the actual HACS UI, the public repository was added as a
custom repository of type Integration and commit `a9c9b5a` was installed. HACS's
stored installation record confirms that commit, and the downloaded card's SHA-256
matches the repository file. After a process restart, the actual HA configuration
flow created ECM using only a synthetic cumulative-energy sensor.

The real Lovelace card rendered in a desktop browser. Its simple form saved an
invented price profile; a frozen report appeared with HTML/CSV export actions.
The profile and report are in the separate application database. There was no
production configuration or production token reuse. This goes beyond the earlier
headless download test; it does not establish mobile UX, full billing, migration
of legacy profiles/reports, or an HAOS restore.

Observed HACS behavior: its first ZIP request for the short commit SHA returned
404, then its existing per-file fallback completed installation. No HACS source
was modified. Verify the installation record and actual files instead of treating
the initial ZIP error alone as a failed installation. No release tag exists yet;
this is a custom-repository development installation, not a catalog beta.

The next test updates this installed copy to the documentation revision containing
this record, restarts HA and compares the existing samples, profile/report digests
and config-entry ID. A documentation-only update exercises HACS replacement and
persistence, not migration between incompatible application schemas. Its outcome
must be recorded after execution, not inferred from successful installation.

Slovenščina: dejanska namestitev prek HACS in prvi ponovni zagon sta uspešna.
Kartica v pravem brskalniku shrani izmišljeni profil in zamrznjeno poročilo.
Produkcija ostaja nespremenjena; to še ni potrditev celotne funkcionalne zamenjave.


**Consolidated status, 23 October 2026:** see [published checks, latest local evidence and remaining gates](validation-status.md). Earlier dated observations below describe their tested revision; they do not imply full application migration or a complete HACS installation transaction.

This is a development custom repository, not a supported beta or a HACS default
catalog entry. Use a disposable HA 2026.10.2 or newer lab with synthetic sources.
Do not install on an instance with an existing `energy_cost_monitor` component:
HACS manages that same directory and can replace the previous implementation.

## Installation and update rehearsal

1. Take a copy of the disposable lab configuration before testing package updates.
2. In HACS, open Custom repositories, add
   `https://github.com/MrCodeLabs/ha-energy-cost-monitor`, category Integration.
3. Select the explicitly tested revision. During development, changes on a PR
   branch are not automatically included in the default-branch download.
4. Download, restart the lab, then add Energy Cost Monitor in Devices & services.
   Paste `examples/minimal.json` as the source configuration and provide a
   synthetic `sensor.example_import_energy` in kWh.
5. Check the collection sensor and record the ledger contents. Download a newer
   tested revision, restart, and verify the same entry and earlier measurements.
6. For rollback, stop the lab, retain its current `.storage` including the ledger,
   restore the previously tested component code and restart. Downgrades across
   storage versions require a specific migration/rollback procedure; never erase
   the ledger to bypass an incompatibility error.

Removing the config entry retains the ledger. Removing package files through
HACS is not a data migration. Keep data outside the integration directory so
package replacement cannot erase it. Do not enable automatic production updates.

The CI HACS check skips **only Brands**, because this is not a catalog submission.
All other HACS checks and hassfest must pass. Brands remains an explicit catalog
gate. The pinned HACS action currently references its upstream `main` container
image internally; pinning its wrapper does not pin that image's contents.

GitHub authentication for an interactive HACS setup must be performed by the
operator using HACS's normal flow. Production HA credentials/configuration must
not be copied into a test instance. See the
[official custom-repository instructions](https://www.hacs.dev/docs/faq/custom_repositories/).

## Slovenščina

Paket je namenjen samo razvojnemu HACS laboratoriju. Stare integracije na tvojem
produkcijskem HA ne prepisuj: domena in imenik sta enaka. Namestitev in nadgradnjo
preveri na sintetičnih podatkih, po ponovnem zagonu primerjaj vnos in zgodovino.
Pred povratkom ohrani tudi nove podatke; brisanje zbirke ni migracija. Prijavo v
GitHub za HACS opravi po običajnem postopku, brez kopiranja produkcijskih žetonov.
Vključitev v privzeti katalog in produkcijski prehod ostajata ločena koraka.
