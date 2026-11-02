# Vodič za nove uporabnike

Posodobljeno 2. 11. 2026 · [English](getting-started.md) · [Pregled projekta](../README.sl.md)

## 1. Pred namestitvijo

To je razvojna integracija za ločen testni HA, ne dodatek (add-on). Preverjeno
okolje je HA Core 2026.10.2 s HACS 2.0.5; preizkus ne potrjuje drugih različic.
Potrebuješ skrbniški račun HA, delujoč HACS in obstoječe energijske senzorje.
Če HACS še nimaš, uporabi [uradna navodila](https://www.hacs.dev/docs/use/).
Produkcijskih poverilnic ne kopiraj v testno namestitev.

Pripravi kumulativna števca hišne porabe in prevzema iz omrežja, njuni dejanski
enoti ter smiselne meje moči in svežine. Izbirne zmožnosti potrebujejo ustrezne
števce/signale. Moč v kW ni kumulativna energija v kWh. Začneš lahko samo z viri,
cene pa dodaš pozneje. Zasebno pripravi veljavnost pogodbe, cene prevzema/oddaje,
naročnino ter po potrebi dogovorjene moči in regionalne postavke.
Prazno pomeni neznano; ničla pomeni dejansko ničelno postavko.

**Ne nameščaj čez obstoječo komponento `energy_cost_monitor`.** HACS zamenja isti
imenik. Pred namestitvijo naredi kopijo testnega HA; selitev produkcijskega
prototipa je ločen postopek. Podprt je en vnos integracije na namestitev HA.

## 2. Prenos prek HACS

1. Odpri HACS in zgornji desni meni → **Custom repositories** (repozitoriji po meri).
2. Dodaj `https://github.com/MrCodeLabs/ha-energy-cost-monitor`, vrsta **Integration**.
3. Odpri **Energy Cost Monitor (development)** in prenesi paket. Zapiši commit,
   ki ga prikaže HACS; `532012e` je preverjena različica z dne 2. novembra.
   Poznejši prenos iz `main` lahko vsebuje nove spremembe; odprti PR ni vključen samodejno.
4. Ponovno zaženi testni Home Assistant.
5. Izberi **Nastavitve → Naprave in storitve → Dodaj integracijo → Energy Cost Monitor**.

Postopek sledi [uradnim navodilom HACS](https://www.hacs.dev/docs/faq/custom_repositories/).
Na tej stopnji ni stabilne izdaje ali vključitve v privzeti katalog.

## 3. Izbor virov in odpiranje plošče

Izberi **Voden izbor senzorjev**, označi samo zmožnosti, za katere imaš podatke,
in za vsak vir izberi entiteto, enoto, vrsto meritve, največjo starost poročila in
smiselno moč. Spremljevalni signali svežine so izbirni; uporabi jih le, če zanesljivo
potrjujejo svežino števca. Preglej preslikavo in shrani.

Pri minimalni postavitvi brez sončne elektrarne, hranilnika in oddaje lahko isti
števec pokriva hišo/prevzem z enakimi nastavitvami. Sicer potrebuješ ustrezna ločena
števca. Nedosegljiv senzor ne potrjuje pravilnosti izbrane enote.

Skrbnikom se samodejno prikaže stranska plošča **Energy Cost Monitor**.
Ročen vpis vira kartice ali YAML ni potreben. Plošča ima trenutno slovenske oznake.
JSON in ročna kartica Lovelace ostajata izbirni napredni možnosti.

## 4. Nastavitev funkcij

| Zavihek | Postopek |
| --- | --- |
| **Cene** | Poimenuj profil, dodaj ponudbo in različico pogodbe, vnesi veljavnost, naročnino ter obdobja cen prevzema/oddaje. Izberi enote in vire; potrdi samo preverjene cene. Izberi **Shrani cenovni profil**. |
| **Profili** | Preglej različice ali aktiviraj prejšnjo. Spremembe ustvarijo novo različico, zamrznjena poročila ohranijo stare predpostavke. Napredni urejevalnik JSON je izbiren. |
| **EV in obračun** | Po potrebi vključi izračun EV iz števca ter nastavi razmike, moč in tolerance. Pri regionalnih nastavitvah dodaj datume, blokovne tarife, dogovorjene moči, dajatve, DDV in režim presežne moči. Izberi **Shrani EV in obračun**. |
| **Študija** | Nastavi časovni pas, mesece, uvajanje, pokritost in dnevno kontrolo; izberi **Začni uvajanje študije**. Zahtevano dnevno referenco hiše izberi med viri integracije. |
| **Poročila** | Izberi obdobje prikaza in **Zamrzni prikazano obdobje**. Odpri/prenesi zamrznjeno poročilo HTML ali CSV. |

Časi cen potrebujejo odmik, npr. `2026-01-01T00:00:00+01:00`; konec obdobja je
izključen. Uporabi pravi odmik za izbrani datum. Regionalna obdobja vnašaš kot
datume. Priključna moč **ni** dogovorjena obračunska moč po blokih.

Za izmišljeno vajo lahko vneseš prevzem `0.15` EUR/kWh in naročnino `2` EUR/mesec
brez DDV z izrecnimi datumi veljavnosti. Vir označi »Izmišljeni primer« in pusti
potrditev izključeno. To niso dejanske tarife ali priporočene hišne nastavitve;
pred razlago resničnih rezultatov jih zamenjaj.

Izbirna cena **Referenčni indeks Energy-Charts + pribitek** nadomesti vnesene cene
prevzema znotraj veljavnosti pogodbe. Območje in pribitek izbereš v obrazcu.
Ponudniku se pošljeta območje/datum, ne meritve ali profili; vidi omrežni naslov
odjemalca. Zajem in dopolnjevanje zgodovine sta postopna. Indeks ostaja referenca,
ne potrjena dobaviteljeva formula.

EV načini se opazujejo, ne krmilijo. Uvajanje študije se zaključi šele po uspešni
kontroli kakovosti; manjkajoča zahtevana dnevna referenca ga zadrži. V živo sta
preverjena uvajanje in ohranitev stanja, mesečna/končna poročila s simuliranim časom.
Regionalni model velja samo za Slovenijo **2026**. Dobroimetje, izplačila in končni
znesek za plačilo še niso dokončani. HTML ohrani regionalne dokaze; CSV trenutno
izvozi energijske/dobavne vrstice, ne enakovrednega celotnega regionalnega obračuna.

## 5. Izbirni uvoz stare zgodovine

Pri novi namestitvi to preskoči. **Uvoz zgodovine** sprejme podprto kopijo SQLite
starega Energy Cost Monitorja, ne poljubne zbirke HA recorder ali CSV.
Uporabi konsistentno kopijo; datoteke ne kopiraj med aktivnim pisanjem vanjo.

1. Pripravi kopijo obeh trenutnih shramb ECM in konfiguracije HA.
2. V obrazcu izberi staro kopijo SQLite in preglej predogled.
3. Preslikaj vse zahtevane vloge, izberi profil in izključni končni datum primerjave
   starih cen. Izberi, ali naj se pretvorjeni profil aktivira.
4. Potrdi pregled in izberi **Uvozi preverjeno zgodovino**.
5. Preveri število uvoženih zapisov, oznako kopije, profile in arhivirana poročila.

Datoteka se naloži v tvoj HA. Izvirne vrstice se ohranijo; prekrivanje z novimi
meritvami, nepodprta ali že uvožena zgodovina se zavrne. Pred uvozom se kopirata obe
shrambi. Naloženi osnutek lahko nadaljuješ ali zavržeš brez spremembe izvirne
lokalne datoteke. Stara študija in regionalne nastavitve se ne aktivirajo samodejno;
preglej in nastavi jih ločeno. To ni obnova celotnega HA.
[Tehnične omejitve uvoza](application-migration.md).

## 6. Preverjanje delovanja

- Preveri senzor kakovosti zajema in čas zadnjega vzorca na plošči.
- Počakaj na poročila števcev in zaključen četrturni interval. Začetne, zastarele
  ali nepopolne meritve lahko pravilno pokažejo **neznano**.
- Ponovno odpri nastavitve ter preveri aktivni profil, obdobja, enote in potrditve.
- Zamrzni testno poročilo in preveri njegovo ohranitev po testnem ponovnem zagonu.
- Loči znani del od celote; nobeden sam po sebi ni znesek dobaviteljevega računa.
  Nepreverjenih postavk ne potrjuj samo zato, da izgine opozorilo.

## 7. Posodobitve, kopije in odstranitev

Pred posodobitvijo zapiši commit in naredi konsistentno kopijo HA s konfiguracijo
ter **obema** zasebnima datotekama: `.storage/energy_cost_monitor.sqlite3` in
`.storage/energy_cost_monitor_application.sqlite3`. Pred kopiranjem datotek ustavi
integracijo/HA. Stari obnovitveni ZIP samo meritev ne vsebuje aplikacijske shrambe.
Izvozi tudi pomembna poročila; izvozi ne nadomestijo celotne kopije.

Posodobi prek HACS, ponovno zaženi HA in ponovi zgornje preverjanje ohranjenih
meritev, profilov in poročil. Razvojnega paketa ne posodabljaj samodejno.
Pri povratku ustavi zajem, ohrani trenutni shrambi z novimi meritvami in obnovi
združljivo kopijo kode, konfiguracije ter obeh shramb. Starejša koda morda ne bere
nove sheme. Zbirke ne briši zaradi obhoda te zaščite. Obnova celotnega HAOS s tem
laboratorijem še ni potrjena.

Za prenehanje uporabe onemogoči vnos med napravami in storitvami. Za odstranitev
najprej ohrani kopijo, odstrani vnos, nato paket prek HACS in ponovno zaženi HA.
Odstranitev vnosa ohrani zgodovino; odstranitev kode ni izbris podatkov ali selitev
nazaj v staro aplikacijo. Sprememba identitete virov po začetku zajema zahteva
selitev, ki je obrazec za ponovno nastavitev še ne omogoča.

## Težave in povratne informacije

| Težava | Kaj preveriti |
| --- | --- |
| Integracija/plošča manjka | Prenos HACS, ponovni zagon, dodajanje integracije, skrbniški račun in osvežitev brskalnika. |
| Neznani zneski | Svežina/enote senzorjev, zaključeni intervali, pokritost, datumi cen in manjkajoče/nepotrjene postavke. |
| Študija ostane v uvajanju | Pokritost in zahtevana dnevna referenca; čakanje je lahko pravilno. |
| Ponovna nastavitev/uvoz zavrnjena | Omejitve identitete in prekrivanja; ohrani podatke ter popravi preslikavo, ne briši zbirk. |
| Obrazec zavrnjen | Številke, enote, odmiki datumov, veljavnost in prekrivajoča se obdobja. |

V [prijavi težave](https://github.com/MrCodeLabs/ha-energy-cost-monitor/issues)
navedi različici HA/HACS, commit, korake ter pričakovani/dejanski rezultat.
Uporabi izmišljene primere; izpusti osebne podatke, žetone, zasebne dnevnike,
račune in zbirke. [Dokazi](acceptance-2026-11-02.md) in [načrt](../ROADMAP.md)
opredeljujejo omejitve. Starejši tehnični zapisi niso vodič za prvo namestitev.
