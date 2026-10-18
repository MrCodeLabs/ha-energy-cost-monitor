# Energy Cost Monitor za Home Assistant

Samostojen projekt za primerjavo dobavnih scenarijev elektrike, prikaz kakovosti meritev in ponovljiva poročila na podlagi podatkov Home Assistanta.

**Stanje 18. 10. 2026: vzpostavljen javni projekt in razvojni načrt. Namestljive integracije, kartice, izdaje ali podpore HACS v tem repozitoriju še ni.**

Obstoječi zasebni prototip že vsebuje zbiralnik, obračunsko jedro, prijavljeni API, kartico, poročila in teste. Pred javnim prenosom je treba odstraniti hišne odvisnosti ter preveriti namestitev, nadgradnje in obnovo podatkov.

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

Dokumentacija še ni navodilo za namestitev. Za osnovne stroškovne senzorje najprej preveri obstoječa Dynamic Energy Cost in Powercalc, povezana v [angleškem README](README.md).
