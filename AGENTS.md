# Pravila projekta

- Z uporabnikom komuniciraj v slovenščini. Začni v README.md, README.sl.md in ROADMAP.md; tehnični vstop je docs/architecture.md.
- Javna dokumentacija ima angleško osnovo; ključna uporabniška navodila ohrani tudi v slovenščini.
- Upoštevaj dejansko stanje: pred prvo javno implementacijo ne oglašuj namestitve, podpore HACS ali združljivosti.
- Pred spremembo integracije ali kartice preglej aktualne izvirne projekte, kodo, dokumentacijo, issue/PR, vzdrževanost in morebitni ločeni frontend istega avtorja. Primerjavo in konkretno vrzel zapiši v docs/alternatives.md. Obstoječi ustrezen izvirnik ima prednost za prispevek.
- Uporabniške entitete, tarife, pragove in zmožnosti konfiguriraj. Zasebni inventar, topologija, IP/MAC, produkcijski dnevniki, računi, zbirke in poverilnice ne sodijo v javni repo. Primeri in testi so sintetični.
- Ohrani izvor, avtorstvo in licence prenesene kode. Ne prenašaj zasebne Git zgodovine.
- Monitor je bralen: ne dodajaj krmiljenja naprav brez izrecno naročenega obsega. Manjkajočih podatkov ne pretvarjaj v ničle ali potrjen račun.
- Razvijaj na ločenih vejah in preveri spremembi primerne teste. Commit/push, PR in izdajo izvedi samo v izrecno naročenem obsegu. Produkcijska namestitev zahteva ločen postopek.
- Potrjene spremembe dokumentiraj z datumom, rezultatom, omejitvami in naslednjim korakom; razvojno zgodovino vodi v CHANGELOG.md in docs/, ne tukaj.
