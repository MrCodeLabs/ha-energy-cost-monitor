# HACS development package

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
