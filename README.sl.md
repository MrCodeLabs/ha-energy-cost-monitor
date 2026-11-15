<div align="center">

<img src="custom_components/energy_cost_monitor/brand/icon.png" alt="Energy Cost Monitor" width="160" />

# Energy Cost Monitor za Home Assistant

[![Marketplace: repozitorij po meri](https://img.shields.io/badge/Marketplace-Custom-41BDF5.svg)](https://www.home-assistant.io/integrations/marketplace/#custom-repositories)
[![0.1.0-beta.1](https://img.shields.io/badge/beta-0.1.0--beta.1-007ec6.svg)](https://github.com/MrCodeLabs/ha-energy-cost-monitor/releases/tag/0.1.0-beta.1)
[![Licenca MIT](https://img.shields.io/badge/license-MIT-97CA00.svg)](LICENSE)
[![Podpri prek Revoluta](https://img.shields.io/badge/Revolut-podpri-007ec6.svg?logo=revolut&logoColor=white)](https://revolut.me/alesvucina)
[![Podpri prek PayPala](https://img.shields.io/badge/PayPal-podpri-007ec6.svg?logo=paypal&logoColor=white)](https://paypal.me/AlesVucina)
[![Odpri Energy Cost Monitor v Home Assistantu](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MrCodeLabs&repository=ha-energy-cost-monitor&category=integration)

</div>

Primerjaj dobavne ponudbe elektrike, spremljaj meritve in EV seje ter shrani
ponovljiva poročila iz obstoječih senzorjev Home Assistanta. Integracija podatke
bere in ne krmili naprav.

**Javna beta.** Dodaj Energy Cost Monitor kot repozitorij po meri v Home Assistant
Marketplaceu in vključi predizdaje. Za beto uporabi ločeno testno namestitev.

**[Začni tukaj: namestitev in uporabniški vodič](docs/getting-started.sl.md)** ·
[English](README.md)

## Kaj je novega v različici 0.1.0-beta.1

- **Vodena nastavitev.** Izberi obstoječe senzorje energije in odpri ploščo,
  ki se samodejno doda v stransko vrstico.
- **Primerjava dobavnih ponudb.** Nastavi cene in naročnine ter shrani poročila
  v obliki HTML ali CSV.
- **Spremljanje polnjenja EV.** Beleži seje z ustreznim kumulativnim števcem.
- **Nadaljevanje uvožene študije.** Ob uvozu podprte kopije SQLite obnovi prvotni
  razpored in poveži arhivirana poročila.

[Opombe izdaje](https://github.com/MrCodeLabs/ha-energy-cost-monitor/releases/tag/0.1.0-beta.1) ·
[Dnevnik sprememb](CHANGELOG.md)

## Kaj lahko nastaviš

- Voden izbor senzorjev; sončna elektrarna, hranilnik, EV in TČ so izbirni.
- Samodejno skrbniško ploščo z obrazci za cene, profile in poročila.
- Obdobja cen prevzema/oddaje, naročnino in izbirne referenčne cene.
- EV izračun iz števca, opažene načine, regionalne postavke za Slovenijo 2026
  ter uvajanje študije z mesečnimi in končnimi poročili.
- Voden uvoz podprte kopije SQLite starega Energy Cost Monitorja.

Za podprti postopek ni treba dopisovati kode ali urejati JSON/YAML. Plošča je
privzeto angleška; slovenski jezik uporabnika HA vključi slovenski prevod.
Drugi jeziki uporabljajo angleščino. Potreben je skrbniški račun. Podprt je en vnos integracije
na namestitev HA.

## Kaj je preverjeno in kaj še manjka

Funkcije so združene v `main` (`532012e`) prek
[PR #11](https://github.com/MrCodeLabs/ha-energy-cost-monitor/pull/11).
V ločenem HA 2026.10.2 so preverjeni obrazci, sintetični uvoz, izdelava poročila,
krmilni elementi študije ter prenos prek HACS in ponovni zagon. Posodobitev je
ohranila stare meritve, štiri različice profilov in dve poročili; vseh 27 datotek
paketa se je ujemalo s preverjeno kodo. Uspešnih je 207 Python testov in CI na
veji, PR ter main. [Dokazi in omejitve](docs/acceptance-2026-11-02.md).

To ne potrjuje vseh različic HA ali obnove celotnega HAOS. Odprti ostajajo
primerjava z računom, začetno/preneseno dobroimetje, izplačila, regionalna pravila
za 2027 ter preverjanje pri neodvisnem uporabniku. Manjkajoče vrednosti ostanejo
neznane. **Obstoječe produkcijske integracije še ne zamenjuj.**

## Zasebnost in pomoč

Nastavitve, meritve in poročila ostanejo v tvojem HA. Izbirni zajem Energy-Charts
pošlje območje/datum ponudniku, ki vidi tudi omrežni naslov odjemalca. Javni repo
vsebuje splošno kodo in izmišljene primere.

Pri [prijavi težave](https://github.com/MrCodeLabs/ha-energy-cost-monitor/issues)
navedi različici HA/HACS, nameščeni commit in anonimizirane korake. Ne prilagaj
žetonov, zasebnih dnevnikov, računov, identifikatorjev merilnih mest ali hišnih baz.

Razvojne podrobnosti: [načrt](ROADMAP.md), [zgodovina preverjanj](docs/validation-status.md),
[spremembe](CHANGELOG.md), [arhitektura](docs/architecture.md),
[razvoj](docs/development.md) in [izvor kode](docs/provenance.md).
Licenca: [MIT](LICENSE). Datirani starejši zapisi so razvojna zgodovina;
za prvo namestitev uporabi zgornji uporabniški vodič.
