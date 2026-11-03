# Energy Cost Monitor za Home Assistant

Primerjaj dobavne ponudbe elektrike, spremljaj meritve in EV seje ter shrani
ponovljiva poročila iz obstoječih senzorjev Home Assistanta. Integracija podatke
bere in ne krmili naprav.

**Razvojni predogled — posodobljeno 2. 11. 2026.** Namesti ga prek HACS kot
repozitorij po meri v ločeni testni namestitvi. To še ni stabilna izdaja, vnos v
privzetem katalogu HACS ali kalkulator celotnega računa.

**[Začni tukaj: namestitev in uporabniški vodič](docs/getting-started.sl.md)** ·
[English](README.md)

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
