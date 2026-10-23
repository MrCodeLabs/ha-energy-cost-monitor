# Energy Cost Monitor za Home Assistant

Samostojen projekt za primerjavo dobavnih scenarijev elektrike, prikaz kakovosti meritev in ponovljiva poročila na podlagi podatkov Home Assistanta.

**Stanje 23. 10. 2026: nastavljivi viri, trajno merilno jedro, dobavni scenariji in razvojni HA adapter za eno instanco.** Adapter ima izolirane teste življenjskega cikla; celoten HA še ni preizkušen. Izdaje, kartice in podpore HACS še ni.

Lastnik je potrdil lastno avtorstvo in dovolil pregledani prenos pod MIT. [Razvojni model virov](docs/source-configuration.md) je povezan z [merilnim jedrom](docs/accounting.md): prirastki, ocenjena četrturna razporeditev, pokritost, vrzeli, ponastavitve in ločena zbirka SQLite. Primer minimalne hiše ne potrebuje EV, hranilnika, sončne elektrarne ali TČ.

[Dobavni scenariji](docs/pricing.md) dodajajo veljavnost cen prevzema/oddaje, naročnino, negativne cene in primerjavo na istih pokritih intervalih. Manjkajoči podatki ostanejo označeni. Izračun je v EUR brez DDV, omrežnine in dajatev; ni celoten račun.

[HA adapter](docs/ha-adapter.md) uporablja čase dejanskih poročil senzorjev, ločeno zbirko SQLite ter nastavitvene obrazce in diagnostični senzor zajema. Reload/unload počaka na zapis v zbirko in odstrani poslušalce. Spremembe identitete virov brez migracije so zavrnjene; možnosti omogočajo spremembo intervala zajema. Pravi HA preizkus, nadgradnje in obnova ostajajo odprti.

## Prva ciljna različica

- Branje obstoječih senzorjev, brez krmiljenja naprav.
- Nastavljivi energijski viri; EV, hranilnik in TČ so izbirne zmožnosti, ne obvezna oprema vsakega uporabnika.
- Slovenski tarifni model z jasno veljavnostjo in izvorom cenikov.
- Primerjava prevzema, oddaje in naročnin; ostale postavke le ob ustreznih podatkih.
- Vidne vrzeli, ponastavitve števcev, referenčne cene in negotove ocene.
- Poročila, ki ohranijo takratne podatke in predpostavke.

Podroben [razvojni načrt](ROADMAP.md) loči že vzpostavljen projekt od prihodnjih funkcij. [Primerjava obstoječih rešitev](docs/alternatives.md) pojasni predvideni obseg. [Dnevnik izkušenj](docs/experience.md) bo ločil meritve, simulacije, predpostavke in še nepreverjene rezultate.

## Zasebnost in izvor

Javna razvojna kopija vsebuje samo pregledano splošno kodo in izmišljene primere. Hišne nastavitve, zbirke, računi, dostopi in zasebna zgodovina ostanejo zunaj javnega repozitorija. Produkcijska namestitev se ob vzpostavitvi tega projekta ne spreminja.

Navodila adapterja so namenjena samo ločenemu razvojnemu laboratoriju z izmišljenimi senzorji. Produkcijskega prototipa ne prepisuj. Za osnovne stroškovne senzorje najprej preveri Dynamic Energy Cost in Powercalc, povezana v [angleškem README](README.md).

## Razvojna preverjanja

GitHub Actions CI preverja kodo z Ruff in izvaja sintetične teste na Linuxu/Windowsu s Python 3.12–3.14. Dependabot tedensko predlaga posodobitve razvojnih odvisnosti in Actions; združitev ostaja ročna. Lokalno je uspešnih 81 testov, [prvi PR zagon na GitHubu](https://github.com/MrCodeLabs/ha-energy-cost-monitor/actions/runs/39472304035) pa je 20. 10. 2026 uspešno zaključil celotno matriko.

CI nima produkcijske namestitve. Novi lokalni testi vključujejo izolirane pogodbe adapterja; pravi HA, hassfest in HACS še niso preverjeni. Aktivno pravilo `main-ci` za vejo `main` zahteva PR, posodobljeno osnovo in uspešen rezultat `CI result`. Pravilo je nastavitev repozitorija; sam workflow je ne vključi v drugih kopijah projekta. Ukazi za lokalno preverjanje in omejitve so v [razvojnih navodilih](docs/development.md#continuous-integration).
