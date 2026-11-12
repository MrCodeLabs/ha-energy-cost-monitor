/* English source messages; Slovenian translation selected from the HA user language. */
const ECM_SL = {
  "1 day": "1 dan",
  "Not configured": "Ni nastavljena",
  "Warm-up": "Uvajanje",
  "Running": "Poteka",
  "Complete": "Končana",
  "Cancelled": "Ustavljena",
  "Insufficient data": "Premalo podatkov",
  "Passed": "Uspešno",
  "Mismatch": "Neujemanje",
  "unknown": "neznano",
  "still open": "še odprta",
  "Overview": "Pregled",
  "EV sessions": "EV seje",
  "Reports": "Poročila",
  "Profiles": "Profili",
  "Prices": "Cene",
  "EV and billing": "EV in obračun",
  "Study": "Študija",
  "History import": "Uvoz zgodovine",
  "Waiting for data …": "Čakam na podatke …",
  "Data unavailable. An administrator account and a loaded integration are required.": "Podatki niso dosegljivi. Potreben je skrbniški račun in naložena integracija.",
  "Supply costs and separate regional estimate · not an invoice or amount payable": "Dobavni stroški in ločena regionalna ocena · ni račun ali znesek za plačilo",
  "Price source currently unavailable. Measurement collection continues.": "Cenovni vir trenutno ni dosegljiv. Meritve se zbirajo naprej.",
  "Add a supply-scenario profile to compare costs.": "Dodaj profil dobavnih scenarijev za primerjavo stroškov.",
  "confirmed supply rates": "potrjene dobavne postavke",
  "reference or incomplete data": "referenčni ali nepopolni podatki",
  "Estimate based on HA measurements, not an amount payable.": "Ocena po HA meritvah, ne znesek za plačilo.",
  "Energy-Charts.info: reference index; agreement with the supplier invoice is not confirmed.": "Energy-Charts.info: referenčni indeks; ujemanje z dobaviteljevim računom ni potrjeno.",
  "No EV sessions detected in the selected period.": "V izbranem obdobju ni zaznanih EV sej.",
  "Archived legacy session · original calculation": "Arhivirana seja stare aplikacije · prvotni izračun",
  "Events and modes (observation only)": "Dogodki in načini (samo opazovanje)",
  "Partial session: gaps or unallocated energy at interval boundaries.": "Delna seja: vrzeli ali neuvrščena energija na robovih intervalov.",
  "Covered session intervals.": "Pokriti intervali seje.",
  "A frozen report retains the data, profile and price assumptions at capture time.": "Zamrznjeno poročilo ohrani podatke, profil in cenovne predpostavke trenutka izdelave.",
  "Freeze displayed period": "Zamrzni prikazano obdobje",
  "Could not save the report.": "Poročila ni bilo mogoče shraniti.",
  "Archived report · not recalculated": "Arhivirano poročilo · brez ponovnega izračuna",
  "New simple price profile": "Nov enostaven cenovni profil",
  "Profile name": "Ime profila",
  "Valid from (UTC)": "Velja od (UTC)",
  "Valid until (UTC, exclusive)": "Velja do (UTC, izključno)",
  "Import EUR/kWh excluding VAT": "Uvoz EUR/kWh brez DDV",
  "Export EUR/kWh excluding VAT": "Oddaja EUR/kWh brez DDV",
  "Subscription EUR/month excluding VAT": "Naročnina EUR/mesec brez DDV",
  "An empty price means unknown. Enter 0 for a zero subscription. Prices are references until checked against the contract.": "Prazna cena pomeni neznano. Za ničelno naročnino vnesi 0. Cene so referenčne do preverjanja pogodbe.",
  "Prepare profile": "Pripravi profil",
  "Enter a name and a valid period.": "Vnesi ime in veljavno obdobje.",
  "Import a JSON profile with effective dates, prices and sources. Changes create a new version; reports remain unchanged.": "Uvozi JSON profil z datumi veljavnosti, cenami in viri. Sprememba ustvari novo različico; poročila ostanejo nespremenjena.",
  "Advanced settings and profile preview": "Napredne nastavitve in predogled profila",
  "Supply-scenario JSON profile": "JSON profil dobavnih scenarijev",
  "Save new version": "Shrani novo različico",
  "Invalid profile or save failed.": "Profil ni veljaven ali shranjevanje ni uspelo.",
  "Discard draft": "Zavrzi osnutek",
  " · active": " · aktivna",
  "Use this version": "Uporabi to različico",
  "Profile activation failed.": "Aktivacija profila ni uspela.",
  "Subscription after discount (EUR/month excluding VAT)": "Naročnina po popustu (EUR/mesec brez DDV)",
  "Price excluding VAT": "Cena brez DDV",
  "Unit": "Enota",
  "Price source": "Vir cene",
  "Confirmed against contract or invoice": "Potrjeno s pogodbo oziroma računom",
  "Edit offers and periods using forms. Empty prices remain unknown. Effective timestamps need an offset, e.g. 2026-01-01T00:00:00+01:00; the end is exclusive. Changes save a new version.": "Uredi ponudbe in obdobja prek obrazcev. Prazne cene ostanejo neznane. Časi veljavnosti morajo vsebovati časovni odmik, npr. 2026-01-01T00:00:00+01:00; konec je izključen. Spremembe shranijo novo različico.",
  "Time zone (IANA)": "Časovni pas (IANA)",
  "Offer identifier: ": "Identifikator ponudbe: ",
  "Import price": "Cena prevzema",
  "Entered prices": "Vnesene cene",
  "Energy-Charts reference index + markup": "Referenčni indeks Energy-Charts + pribitek",
  "Index zone": "Območje indeksa",
  "Markup EUR/kWh": "Pribitek EUR/kWh",
  "The index replaces entered import prices within contract validity. This is a reference, not a confirmed supplier formula.": "Indeks nadomesti vnesene cene prevzema znotraj veljavnosti pogodb. Gre za referenco, ne potrjeno dobaviteljevo formulo.",
  "Effective from": "Veljavnost od",
  "Effective until": "Veljavnost do",
  "Import": "Prevzem",
  "Export": "Oddaja",
  "Price valid from": "Cena velja od",
  "Price valid until": "Cena velja do",
  "Remove price period": "Odstrani cenovno obdobje",
  "Add period: ": "Dodaj obdobje: ",
  "Remove contract version": "Odstrani različico pogodbe",
  "Add contract version": "Dodaj različico pogodbe",
  "Remove offer": "Odstrani ponudbo",
  "Add offer": "Dodaj ponudbo",
  "Save price profile": "Shrani cenovni profil",
  "Check the name, validity, prices and overlapping periods. The draft is retained.": "Preveri ime, veljavnost, cene in prekrivanje obdobij. Osnutek je ohranjen.",
  "Discard price changes": "Zavrzi cenovne spremembe",
  "Select a consistent legacy Energy Cost Monitor SQLite backup. The file is uploaded only to your HA. Import retains original records and adds history preceding native collection; overlap is refused. Both current stores are privately backed up before writing.": "Izberi konsistentno kopijo SQLite starega Energy Cost Monitorja. Datoteka se naloži samo v tvoj HA. Uvoz ohrani originalne zapise in doda zgodovino pred začetkom novih meritev; prekrivanje je zavrnjeno. Pred zapisom se zasebno shranita kopiji obeh trenutnih zbirk.",
  "Import transfers measurements, supply profiles and archived sessions and reports. Regional settings require separate setup.": "Uvoz prenese meritve, dobavne profile ter arhiv sej in poročil. Regionalne nastavitve nastaviš ločeno.",
  "Continue the legacy study with its original report dates": "Nadaljuj staro študijo z izvirnimi datumi poročil",
  "To continue the study, also activate the converted supply profile.": "Za nadaljevanje študije aktiviraj tudi pretvorjeni dobavni profil.",
  "Legacy study schedule restored.": "Urnik stare študije je obnovljen.",
  "Show uploaded backups": "Prikaži že naložene kopije",
  "List unavailable.": "Seznam ni dosegljiv.",
  "Resume backup preview": "Nadaljuj pregled kopije",
  "Backup unavailable.": "Kopija ni dosegljiva.",
  "Remove uploaded backup": "Odstrani naloženo kopijo",
  "Could not remove the backup.": "Kopije ni bilo mogoče odstraniti.",
  "Legacy database backup (.sqlite3)": "Kopija stare zbirke (.sqlite3)",
  "Upload and preview backup": "Naloži in preglej kopijo",
  "Select a backup file.": "Izberi datoteko kopije.",
  "Could not validate the backup. Use a supported consistent database up to 100 MB.": "Kopije ni bilo mogoče preveriti. Uporabi podprto konsistentno zbirko do 100 MB.",
  "Select measurement": "Izberi meritev",
  "Legacy supply profile": "Stari dobavni profil",
  "Legacy price comparison end (exclusive date)": "Konec primerjave starih cen (izključni datum)",
  "Activate converted supply profile after import": "Po uvozu aktiviraj pretvorjeni dobavni profil",
  "I reviewed the mapping and confirm importing this backup": "Pregledal sem preslikavo in potrjujem uvoz te kopije",
  "Import reviewed history": "Uvozi preverjeno zgodovino",
  "Complete all mappings and the date, then confirm the review.": "Izpolni vse preslikave in datum ter potrdi pregled.",
  "Import failed. Possible reasons include overlap with native collection, previously imported history or invalid settings. Check the data; existing stores are not overwritten.": "Uvoz ni uspel. Možni razlogi so prekrivanje z novimi meritvami, že uvožena zgodovina ali napačne nastavitve. Preveri podatke; obstoječe zbirke se ne prepisujejo.",
  "Discard uploaded backup": "Zavrzi naloženo kopijo",
  "Could not discard the uploaded backup.": "Naložene kopije ni bilo mogoče zavreči.",
  "First create a price profile in the Profiles tab.": "Najprej ustvari cenovni profil v zavihku Profili.",
  "Changes create a new profile version. Frozen reports are preserved.": "Spremembe ustvarijo novo različico profila. Zamrznjena poročila ostanejo ohranjena.",
  "EV calculation from counter increments": "EV izračun iz prirastkov števca",
  "Use sample-level calculation": "Uporabi izračun na ravni vzorcev",
  "EV counter calculation": "Izračun EV iz števca",
  "Maximum sample gap (s)": "Največji razmik vzorcev (s)",
  "Maximum EV power (kW)": "Največja moč EV (kW)",
  "Counter increment tolerance (kWh)": "Toleranca koraka števca (kWh)",
  "Charging power threshold (kW)": "Prag moči polnjenja (kW)",
  "Energy increment threshold (kWh)": "Prag energijskega prirastka (kWh)",
  "Select EV mode sensors in source settings. The integration only records state and never controls the charger.": "Senzorje načinov EV izberi v nastavitvah virov. Integracija samo beleži stanje in nikoli ne upravlja polnilnice.",
  "Network charges, levies and VAT": "Omrežnina, dajatve in DDV",
  "SI 2026 calendar. Enter effective rates excluding VAT and their validity periods. Enter rates with applicable reductions included. Blank means unknown. Connection power is not agreed block power.": "Koledar SI 2026. Vnesi veljavne postavke brez DDV in pripadajoča obdobja. Znižanja vključuje vnesena tarifa. Prazno pomeni neznano. Priključna moč ni dogovorjena moč po blokih.",
  "Valid from": "Velja od",
  "Valid until (exclusive)": "Velja do (izključno)",
  "Rate source": "Vir postavk",
  "Rates checked against a valid contract/invoice": "Postavke preverjene z veljavno pogodbo/računom",
  "Energy EUR/kWh": "Energija EUR/kWh",
  "Power EUR/kW/month": "Moč EUR/kW/mesec",
  "Agreed power kW": "Dogovorjena moč kW",
  "Import VAT (fraction, e.g. 0.22)": "DDV prevzem (delež, npr. 0,22)",
  "Export VAT (fraction)": "DDV odkup (delež)",
  "Operator EUR/kWh": "Operater EUR/kWh",
  "Efficiency EUR/kWh": "Učinkovitost EUR/kWh",
  "Excise EUR/kWh": "Trošarina EUR/kWh",
  "Renewables/CHP basis (kW)": "Osnova OVE/SPTE (kW)",
  "Renewables/CHP EUR/kW/month": "OVE/SPTE EUR/kW/mesec",
  "Excess-power factor": "Faktor presežne moči",
  "Excess-power mode": "Režim presežne moči",
  "Unconfirmed": "Ni potrjeno",
  "Informative, not charged": "Informativno, brez zaračunavanja",
  "Charged": "Zaračunano",
  "Remove version from draft": "Odstrani različico iz osnutka",
  "Add rate period": "Dodaj obdobje postavk",
  "Save EV and billing": "Shrani EV in obračun",
  "Check all limits, effective dates and decimal rates. The draft is retained.": "Preveri vse meje, datume veljavnosti in decimalne postavke. Osnutek ostaja ohranjen.",
  "Discard setting changes": "Zavrzi spremembe nastavitev",
  "After successful warm-up, the study starts at the next local midnight. Monthly and final reports are created automatically; the final summary does not duplicate session lists.": "Začetek se določi po uspešnem uvajanju ob naslednji lokalni polnoči. Mesečna in končno poročilo se ustvarijo samodejno; končni zbirni pregled brez podvajanja seznamov sej.",
  "Stop study (keep reports)": "Ustavi študijo (ohrani poročila)",
  "Could not stop the study.": "Študije ni bilo mogoče ustaviti.",
  "Time zone": "Časovni pas",
  "Number of months": "Število mesecev",
  "Warm-up (hours)": "Uvajanje (ure)",
  "Minimum coverage (fraction)": "Najmanjša pokritost (delež)",
  "Require daily comparison with household sensor": "Zahtevaj dnevno primerjavo s senzorjem hiše",
  "Daily absolute tolerance (kWh)": "Dnevna absolutna toleranca (kWh)",
  "Daily relative tolerance (fraction)": "Dnevna relativna toleranca (delež)",
  "Maximum daily-reference age (s)": "Največja starost dnevne reference (s)",
  "Select the household daily reference in integration sources. Warm-up cannot finish without a valid required reference.": "Dnevno referenco hiše izberi v virih integracije. Brez zahtevane veljavne reference se uvajanje ne zaključi.",
  "Start study warm-up": "Začni uvajanje študije",
  "Invalid study settings.": "Nastavitve študije niso veljavne.",
  "Discard study draft": "Zavrzi osnutek študije",
  "Report download failed.": "Prenos poročila ni uspel.",
  "{0} days": "{0} dni",
  "Period: {0} – {1}": "Obdobje: {0} – {1}",
  "Latest sample: {0}": "Zadnji vzorec: {0}",
  "{0} · coverage {1}": "{0} · pokritost {1}",
  "Known subtotal: {0} · {1}": "Znani del: {0} · {1}",
  "{0} · regional estimate": "{0} · regionalna ocena",
  "Excise basis": "Osnova za trošarino",
  "Imported energy": "Prevzeta energija",
  "Net imported energy over the billing period": "Neto prevzeta energija v obračunskem obdobju",
  "Full billing period for net excise": "Celotno obračunsko obdobje za neto trošarino",
  "Complete import and export readings for net excise": "Popolne meritve prevzema in oddaje za neto trošarino",
  "Total: {0} · known subtotal: {1}": "Celota: {0} · znani del: {1}",
  "Missing: {0}": "Manjka: {0}",
  "Common offer coverage: {0}": "Skupna pokritost ponudb: {0}",
  "{0} · charging {1} · paused {2}": "{0} · polnjenje {1} · premor {2}",
  "Import successful: {0} measurement records, {1} profiles, {2} reports. Pre-import backup: {3}": "Uvoz uspešen: {0} merilnih zapisov, {1} profilov, {2} poročil. Kopija pred uvozom: {3}",
  "Uploaded: {0}": "Naloženo: {0}",
  "Preview: {0} legacy intervals, {1} sessions. History boundary: {2}.": "Pregled: {0} starih intervalov, {1} sej. Meja zgodovine: {2}.",
  "Legacy measurement for {0}": "Stara meritev za {0}",
  "Version {0}": "Različica {0}",
  "Block {0}: {1}": "ČB{0}: {1}",
  "Study state: {0}": "Stanje študije: {0}",
  "Warm-up coverage: {0} · daily check: {1}": "Pokritost uvajanja: {0} · dnevna kontrola: {1}"
};
/* Energy Cost Monitor development card. MIT, Copyright 2026 MrCodeLabs. */
class EnergyCostMonitorCard extends HTMLElement {
  constructor() {
    super(); this.attachShadow({mode: "open"}); this._tab = "overview";
    this._connected = false; this._loading = false; this._generation = 0; this._days = 1; this._draft = null;
  }
  setConfig(config) {
    this._config = {...config}; this._render();
  }
  getCardSize() { return 7; }
  connectedCallback() {
    this._connected = true;
    this._timer = setInterval(() => this._poll(), 30000);
    this._refresh();
  }
  disconnectedCallback() {
    this._connected = false; this._generation++; clearInterval(this._timer);
  }
  set hass(hass) {
    const language = this._language();
    this._hass = hass;
    if (language !== this._language()) {
      const controls = [...this.shadowRoot.querySelectorAll("input,select,textarea")];
      const details = [...this.shadowRoot.querySelectorAll("details")].map(node => node.open);
      this._render();
      const replacements = [...this.shadowRoot.querySelectorAll("input,select,textarea")];
      controls.forEach((node, i) => {
        const replacement = replacements[i];
        if (!replacement || node.type !== replacement.type) return;
        if (node.type === "file") replacement.replaceWith(node);
        else { replacement.value = node.value; replacement.checked = node.checked; }
      });
      this.shadowRoot.querySelectorAll("details").forEach((node, i) => { node.open = details[i]; });
    }
    if (!this._data) this._refresh();
  }
  _language() {
    const language = this._hass?.locale?.language || this._hass?.language || "en";
    return String(language).toLowerCase().split(/[-_]/)[0] === "sl" ? "sl" : "en";
  }
  _status(value) {
    const labels = {not_configured:"Not configured",warmup:"Warm-up",running:"Running",complete:"Complete",cancelled:"Cancelled",insufficient:"Insufficient data",ok:"Passed",mismatch:"Mismatch"};
    return this._t(Object.hasOwn(labels,value) ? labels[value] : String(value));
  }
  _locale() { return this._language() === "sl" ? "sl-SI" : "en-GB"; }
  _t(message, ...values) {
    const key = typeof message === "string" ? message : message.reduce((text, part, i) => text + (i ? `{${i-1}}` : "") + part, "");
    const translated = this._language() === "sl" && Object.hasOwn(ECM_SL, key) ? ECM_SL[key] : key;
    return translated.replace(/\{(\d+)\}/g, (token, index) => index < values.length ? String(values[index]) : token);
  }
  async _api(method, action, data) {
    return this._hass.callApi(method, `energy_cost_monitor/${action}`, data);
  }
  _poll() {
    // Do not collapse open forms or replace their focused controls on a timer.
    if (["profiles", "pricing", "settings", "history"].includes(this._tab) ||
        (this._tab === "study" && !["warmup", "running"].includes(this._study?.state))) return;
    return this._refresh();
  }
  async _refresh() {
    if (!this._connected || !this._hass || this._loading) return;
    if ((this._tab === "profiles" && this._draft !== null) || this._importDraft || this._pricingDraft || this._settingsDraft || this._studyDraft) return;
    this._loading = true; const generation = this._generation;
    try {
      const end = Math.floor(Date.now()/900000)*900;
      const [data, profiles, reports, study] = await Promise.all([
        this._api("GET", `view?start=${end-this._days*86400}&end=${end}`), this._api("GET", "profiles"), this._api("GET", "reports"), this._api("GET", "study")]);
      if (generation !== this._generation) return;
      this._data = data; this._profiles = profiles; this._reports = reports; this._study = study; this._error = null;
    } catch (_) { this._error = "Data unavailable. An administrator account and a loaded integration are required."; }
    finally { this._loading = false; if (this._connected) this._render(); }
  }
  _node(tag, text, parent, className) {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = String(text);
    if (className) node.className = className;
    if (parent) parent.append(node);
    return node;
  }
  _button(text, parent, action) {
    const button = this._node("button", text, parent); button.type = "button";
    button.addEventListener("click", action); return button;
  }
  _number(value, unit="") { return value === null || value === undefined ? this._t("unknown") : `${Number(value).toLocaleString(this._locale(), {maximumFractionDigits: 3})} ${unit}`; }
  _time(value) { return value === null || value === undefined ? this._t("still open") : new Date(value*1000).toLocaleString(this._locale()); }
  _render() {
    const root = this.shadowRoot; root.replaceChildren();
    const style = this._node("style", undefined, root);
    style.textContent = `:host{display:block}ha-card{padding:20px;color:var(--primary-text-color);font-family:var(--paper-font-body1_-_font-family,system-ui)}h2{margin:0 0 6px}nav{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}button{cursor:pointer;padding:9px 12px;border-radius:8px;border:1px solid var(--divider-color,#bbb);background:var(--card-background-color,#fff);color:inherit}button[aria-current=true]{background:var(--primary-color,#176b68);color:white}p{line-height:1.5}.muted{color:var(--secondary-text-color)}.error{color:var(--error-color,#b00020)}article{padding:12px 0;border-top:1px solid var(--divider-color,#ddd)}textarea{box-sizing:border-box;width:100%;min-height:180px;font:12px monospace;color:inherit;background:var(--secondary-background-color,#f5f5f5);border:1px solid var(--divider-color,#bbb);padding:10px}small{display:block;line-height:1.5} .actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}`;
    const card = this._node("ha-card", undefined, root);
    this._node("h2", this._config?.title || "Energy Cost Monitor", card);
    this._node("small", this._t("Supply costs and separate regional estimate \u00b7 not an invoice or amount payable"), card, "muted");
    const periods = this._node("div", undefined, card, "actions");
    for (const days of [1,7,30]) {
      const button = this._button(days === 1 ? this._t("1 day") : this._t`${days} days`, periods, ()=>{this._days=days;this._refresh();});
      button.setAttribute("aria-current",String(this._days===days));
    }
    const nav = this._node("nav", undefined, card);
    for (const [tab,label] of [["overview",this._t("Overview")],["sessions",this._t("EV sessions")],["reports",this._t("Reports")],["profiles",this._t("Profiles")],["pricing",this._t("Prices")],["settings",this._t("EV and billing")],["study",this._t("Study")],["history",this._t("History import")]]) {
      const button = this._button(label,nav,()=>{this._tab=tab;this._render();});
      button.setAttribute("aria-current",String(this._tab===tab));
    }
    if(this._error) this._node("p",this._t(this._error),card,"error");
    if(!this._data){this._node("p",this._t("Waiting for data \u2026"),card);return;}
    const data=this._data;
    if(this._tab==="history") { this._historyForm(card);
    } else if(this._tab==="pricing") { this._pricingForm(card);
    } else if(this._tab==="settings") { this._settingsForm(card);
    } else if(this._tab==="study") { this._studyForm(card);
    } else if(this._tab==="overview") {
      this._node("p",this._t`Period: ${this._time(data.start)} – ${this._time(data.end)}`,card);
      this._node("small",this._t`Latest sample: ${this._time(data.latest_sample)}`,card,"muted");
      if(data.price_error) this._node("p",this._t("Price source currently unavailable. Measurement collection continues."),card,"error");
      if(!data.comparison) this._node("p",this._t("Add a supply-scenario profile to compare costs."),card);
      for(const result of data.comparison?.results || []) {
        const row=this._node("article",undefined,card);
        this._node("strong",result.scenario.identifier,row);
        this._node("p",this._t`${this._number(result.total,"EUR")} · coverage ${this._number(result.coverage*100,"%")}`,row);
        this._node("small",this._t`Known subtotal: ${this._number(result.known_net_subtotal,"EUR")} · ${result.confirmed?this._t("confirmed supply rates"):this._t("reference or incomplete data")}`,row,"muted");
      }
      for(const [name,bill] of Object.entries(data.regional_bills || {})) {
        const row=this._node("article",undefined,card);
        this._node("strong",this._t`${name} · regional estimate`,row);
        this._node("p",this._t`Total: ${this._number(bill.total_gross,"EUR")} · known subtotal: ${this._number(bill.known_reference_gross,"EUR")}`,row);
        for(const [key,value] of Object.entries(bill.components))this._node("small",`${key}: ${this._number(value,"EUR")}`,row);
        const missingLabels={
          excise_partial_period:this._t("Full billing period for net excise"),
          excise_coverage:this._t("Complete import and export readings for net excise"),
        };
        const missing=bill.missing.map(key=>Object.hasOwn(missingLabels,key)?missingLabels[key]:key);
        this._node("small",missing.length?this._t`Missing: ${missing.join(", ")}`:this._t("Estimate based on HA measurements, not an amount payable."),row,"muted");
      }
      if(data.comparison) this._node("p",this._t`Common offer coverage: ${this._number(data.comparison.common_coverage*100,"%")}`,card);
      for(const source of Object.values(data.market_provenance || {})) this._node("small",`${source.source} · ${source.license}`,card,"muted");
      this._node("small",this._t("Energy-Charts.info: reference index; agreement with the supplier invoice is not confirmed."),card,"muted");
    } else if(this._tab==="sessions") {
      if(!data.sessions.length)this._node("p",this._t("No EV sessions detected in the selected period."),card);
      for(const session of [...data.sessions].reverse()) {
        const row=this._node("article",undefined,card), body=session.body;
        if(session.legacy)this._node("small",this._t("Archived legacy session \u00b7 original calculation"),row,"muted");
        this._node("strong",`${this._time(session.start)} → ${this._time(session.end)}`,row);
        this._node("p",this._t`${this._number(body.kwh,"kWh")} · charging ${this._number(body.charging_seconds/60,"min")} · paused ${this._number(body.pause_seconds/60,"min")}`,row);
        for(const [name,total] of Object.entries(body.mode_totals || {}))this._node("small",`${name}: ${this._number(total.kwh,"kWh")} · ${this._number(total.seconds/60,"min")}`,row);
        const events=this._node("details",undefined,row);this._node("summary",this._t("Events and modes (observation only)"),events);
        for(const event of body.events || [])this._node("small",`${this._time(event.ts)} · ${event.state} · ${Object.entries(event.mode || {}).filter(([,v])=>v!==null).map(([k,v])=>`${k}: ${v}`).join(" · ")}`,events);
        this._node("small",body.partial?this._t("Partial session: gaps or unallocated energy at interval boundaries."):this._t("Covered session intervals."),row,"muted");
      }
    } else if(this._tab==="reports") {
      this._node("p",this._t("A frozen report retains the data, profile and price assumptions at capture time."),card);
      this._button(this._t("Freeze displayed period"),card,async()=>{
        try{await this._api("POST","reports",{start:data.start,end:data.end});await this._refresh();}
        catch(_){this._error="Could not save the report.";this._render();}
      });
      for(const report of this._reports || []) {
        const row=this._node("article",undefined,card);
        if(report.legacy)this._node("small",this._t("Archived report \u00b7 not recalculated"),row,"muted");
        this._node("strong",`${this._time(report.start)} – ${this._time(report.end)}`,row);
        const actions=this._node("div",undefined,row,"actions");
        for(const format of ["html","csv"])this._button(format.toUpperCase(),actions,()=>this._download(report.id,format));
      }
    } else {
      const form=this._node("details",undefined,card);
      this._node("summary",this._t("New simple price profile"),form);
      const fields={};
      for(const [key,label,type] of [["name",this._t("Profile name"),"text"],["from",this._t("Valid from (UTC)"),"date"],["until",this._t("Valid until (UTC, exclusive)"),"date"],["price",this._t("Import EUR/kWh excluding VAT"),"number"],["export",this._t("Export EUR/kWh excluding VAT"),"number"],["fee",this._t("Subscription EUR/month excluding VAT"),"number"]]) {
        const wrapper=this._node("label",label,form); wrapper.style.display="block";
        const input=this._node("input",undefined,wrapper);input.type=type;
        if(type==="number")input.step="any"; fields[key]=input;
      }
      this._node("small",this._t("An empty price means unknown. Enter 0 for a zero subscription. Prices are references until checked against the contract."),form,"muted");
      this._button(this._t("Prepare profile"),form,()=>{
        const first=fields.from.value+"T00:00:00Z",last=fields.until.value+"T00:00:00Z";
        if(!fields.name.value.trim() || !Number.isFinite(Date.parse(first)) || Date.parse(last)<=Date.parse(first) || !Number.isFinite(Date.parse(last))) {
          this._error="Enter a name and a valid period.";this._render();return;
        }
        const quote=(value,unit)=>({value:value===""?null:value,unit,source:"User input",status:value===""?"unknown":"reference"});
        const period=value=>({...quote(value,"EUR/kWh"),from:first,until:last});
        this._draft=JSON.stringify({name:fields.name.value,scenarios:[{schema_version:1,id:"my-offer",currency:"EUR",tax_basis:"excluding_vat",timezone:"UTC",versions:[{id:"version-1",from:first,until:last,import:[period(fields.price.value)],export:[period(fields.export.value)],subscription:quote(fields.fee.value,"EUR/month")}]}],indexed_import:{}},null,2);
        this._error=null;this._render();
      });
      this._node("p",this._t("Import a JSON profile with effective dates, prices and sources. Changes create a new version; reports remain unchanged."),card);
      const advanced=this._node("details",undefined,card);advanced.open=this._draft!==null;
      this._node("summary",this._t("Advanced settings and profile preview"),advanced);
      const editor=this._node("textarea",undefined,advanced);editor.setAttribute("aria-label",this._t("Supply-scenario JSON profile"));
      const active=this._profiles?.versions.find(v=>v.id===this._profiles.active);
      editor.value=this._draft ?? JSON.stringify(active?.profile || {name:"My profile",scenarios:[],indexed_import:{}},null,2);
      editor.addEventListener("input",()=>{this._draft=editor.value;});
      this._button(this._t("Save new version"),advanced,async()=>{
        try{await this._api("POST","profiles",JSON.parse(editor.value)); this._draft=null; await this._refresh();}
        catch(_){this._error="Invalid profile or save failed.";this._render();}
      });
      this._button(this._t("Discard draft"),advanced,()=>{this._draft=null;this._render();});
      for(const version of this._profiles?.versions || []) {
        const row=this._node("article",undefined,card);
        this._node("strong",`${version.profile.name}${version.id===this._profiles.active?this._t(" \u00b7 active"):""}`,row);
        if(version.id!==this._profiles.active)this._button(this._t("Use this version"),row,async()=>{
          try{await this._api("POST","profiles",{activate:version.id});await this._refresh();}
          catch(_){this._error="Profile activation failed.";this._render();}
        });
      }
    }
  }

  _field(parent, label, value, type, change) {
    const wrapper=this._node("label",label,parent);wrapper.style.display="block";
    const input=this._node("input",undefined,wrapper);input.type=type;
    if(type==="number")input.step="any";
    if(type==="checkbox")input.checked=!!value;else input.value=value ?? "";
    input.addEventListener("input",()=>change(type==="checkbox"?input.checked:input.value));
    return input;
  }
  _pricingForm(card) {
    const active=this._profiles?.versions.find(v=>v.id===this._profiles.active)?.profile;
    const draft=this._pricingDraft || JSON.parse(JSON.stringify(active || {name:"",scenarios:[],indexed_import:{}}));
    const touch=()=>{this._pricingDraft=draft;};
    const field=(parent,label,obj,key,type="text")=>this._field(parent,label,obj[key],type,value=>{obj[key]=value;touch();});
    const select=(parent,label,value,options,change)=>{
      const wrapper=this._node("label",label,parent);wrapper.style.display="block";
      const input=this._node("select",undefined,wrapper);
      for(const [key,text] of options){const option=this._node("option",text,input);option.value=key;}
      input.value=value;input.addEventListener("change",()=>{change(input.value);touch();});return input;
    };
    const quote=(unit)=>({value:null,unit,source:"User input",status:"unknown"});
    const priceFields=(parent,p,monthly=false)=>{
      this._field(parent,monthly?this._t("Subscription after discount (EUR/month excluding VAT)"):this._t("Price excluding VAT"),p.value,"number",v=>{
        p.value=v===""?null:v;p.status=p.value===null?"unknown":p.status==="unknown"?"reference":p.status;touch();
      });
      if(!monthly)select(parent,this._t("Unit"),p.unit,[["EUR/kWh","EUR/kWh"],["EUR/MWh","EUR/MWh"]],v=>p.unit=v);
      field(parent,this._t("Price source"),p,"source");
      this._field(parent,this._t("Confirmed against contract or invoice"),p.status==="confirmed","checkbox",v=>{
        p.status=p.value===null?"unknown":v?"confirmed":"reference";touch();
      });
    };
    this._node("p",this._t("Edit offers and periods using forms. Empty prices remain unknown. Effective timestamps need an offset, e.g. 2026-01-01T00:00:00+01:00; the end is exclusive. Changes save a new version."),card);
    field(card,this._t("Profile name"),draft,"name");
    for(const scenario of draft.scenarios){
      const box=this._node("fieldset",undefined,card);this._node("legend",scenario.id,box);
      field(box,this._t("Time zone (IANA)"),scenario,"timezone");
      this._node("small",this._t("Offer identifier: ")+scenario.id,box);
      select(box,this._t("Import price"),draft.indexed_import[scenario.id]?"indexed":"fixed",[["fixed",this._t("Entered prices")],["indexed",this._t("Energy-Charts reference index + markup")]],v=>{
        if(v==="indexed")draft.indexed_import[scenario.id]={zone:"SI",markup_eur_kwh:"0"};else delete draft.indexed_import[scenario.id];
      }).addEventListener("change",()=>this._render());
      const binding=draft.indexed_import[scenario.id];
      if(binding){
        select(box,this._t("Index zone"),binding.zone,["SI","AT","DE-LU","HR","IT-North","HU"].map(v=>[v,v]),v=>binding.zone=v);
        field(box,this._t("Markup EUR/kWh"),binding,"markup_eur_kwh","number");
        this._node("small",this._t("The index replaces entered import prices within contract validity. This is a reference, not a confirmed supplier formula."),box);
      }
      for(const version of scenario.versions){
        const group=this._node("fieldset",undefined,box);this._node("legend",version.id,group);
        field(group,this._t("Effective from"),version,"from");field(group,this._t("Effective until"),version,"until");
        priceFields(group,version.subscription,true);
        for(const [direction,label] of [["import",this._t("Import")],["export",this._t("Export")]]){
          const section=this._node("details",undefined,group);this._node("summary",label,section);
          for(const period of version[direction]){
            const row=this._node("fieldset",undefined,section);
            field(row,this._t("Price valid from"),period,"from");field(row,this._t("Price valid until"),period,"until");priceFields(row,period);
            this._button(this._t("Remove price period"),row,()=>{version[direction].splice(version[direction].indexOf(period),1);touch();this._render();});
          }
          this._button(this._t("Add period: ")+label,section,()=>{version[direction].push({...quote("EUR/kWh"),from:version.from,until:version.until});touch();this._render();});
        }
        this._button(this._t("Remove contract version"),group,()=>{scenario.versions.splice(scenario.versions.indexOf(version),1);touch();this._render();});
      }
      this._button(this._t("Add contract version"),box,()=>{
        let n=1;while(scenario.versions.some(v=>v.id===`version-${n}`))n++;
        scenario.versions.push({id:`version-${n}`,from:"",until:"",import:[],export:[],subscription:quote("EUR/month")});touch();this._render();
      });
      this._button(this._t("Remove offer"),box,()=>{draft.scenarios.splice(draft.scenarios.indexOf(scenario),1);delete draft.indexed_import[scenario.id];touch();this._render();});
    }
    this._button(this._t("Add offer"),card,()=>{
      let n=1;while(draft.scenarios.some(s=>s.id===`offer-${n}`))n++;
      draft.scenarios.push({schema_version:1,id:`offer-${n}`,currency:"EUR",tax_basis:"excluding_vat",timezone:this._hass?.config?.time_zone || "UTC",versions:[]});touch();this._render();
    });
    this._button(this._t("Save price profile"),card,async()=>{
      touch();try{this._profiles=await this._api("POST","profiles",draft);this._pricingDraft=null;this._error=null;this._render();await this._refresh();}
      catch(_){this._error="Check the name, validity, prices and overlapping periods. The draft is retained.";this._render();}
    });
    this._button(this._t("Discard price changes"),card,()=>{this._pricingDraft=null;this._error=null;this._render();});
  }
  _historyForm(card) {
    this._node("p",this._t("Select a consistent legacy Energy Cost Monitor SQLite backup. The file is uploaded only to your HA. Import retains original records and adds history preceding native collection; overlap is refused. Both current stores are privately backed up before writing."),card);
    this._node("small",this._t("Import transfers measurements, supply profiles and archived sessions and reports. Regional settings require separate setup."),card);
    if(this._importResult)this._node("p",this._t`Import successful: ${this._importResult.converted_role_intervals} measurement records, ${this._importResult.profiles} profiles, ${this._importResult.reports} reports. Pre-import backup: ${this._importResult.backup}`,card);
    if(this._importResult?.study_resumed)this._node("p",this._t("Legacy study schedule restored."),card);
    if(!this._importDraft){
      this._button(this._t("Show uploaded backups"),card,async()=>{
        try{this._uploads=await this._api("GET","history");this._render();}
        catch(_){this._error="List unavailable.";this._render();}
      });
      for(const pending of this._uploads || []){
        const row=this._node("article",this._t`Uploaded: ${this._time(pending.created)}`,card);
        this._button(this._t("Resume backup preview"),row,async()=>{
          try{const preview=await this._api("POST","history",{command:"resume",id:pending.id});this._importDraft={...preview,mapping:{},horizon:"",profile:preview.profiles[0],activate:false,confirm:false};this._render();}
          catch(_){this._error="Backup unavailable.";this._render();}
        });
        this._button(this._t("Remove uploaded backup"),row,async()=>{
          try{await this._api("POST","history",{command:"discard",id:pending.id});this._uploads=this._uploads.filter(x=>x.id!==pending.id);this._render();}
          catch(_){this._error="Could not remove the backup.";this._render();}
        });
      }
      const label=this._node("label",this._t("Legacy database backup (.sqlite3)"),card);
      const file=this._node("input",undefined,label);file.type="file";file.accept=".sqlite3,.sqlite,.db";
      const upload=this._button(this._t("Upload and preview backup"),card,async()=>{
        const selectedFile = label.querySelector("input");
        if(!selectedFile.files?.length){this._error="Select a backup file.";this._render();return;}
        upload.disabled=true;
        try{
          const body=new FormData();body.append("file",selectedFile.files[0]);
          const response=await this._hass.fetchWithAuth("/api/file_upload",{method:"POST",body});
          if(!response.ok)throw Error("upload_failed");
          const uploaded=await response.json();
          const preview=await this._api("POST","history",{command:"preview",file_id:uploaded.file_id});
          this._importDraft={...preview,mapping:{},horizon:"",profile:preview.profiles[0],activate:false,confirm:false};this._error=null;
        }catch(_){this._error="Could not validate the backup. Use a supported consistent database up to 100 MB.";}
        this._render();
      });return;
    }
    const draft=this._importDraft;
    this._node("p",this._t`Preview: ${draft.counts.intervals} legacy intervals, ${draft.counts.sessions} sessions. History boundary: ${this._time(draft.cutover)}.`,card);
    for(const role of draft.roles){
      const label=this._node("label",this._t`Legacy measurement for ${role}`,card);label.style.display="block";
      const input=this._node("select",undefined,label);
      for(const value of ["",...draft.metrics]){const option=this._node("option",value||this._t("Select measurement"),input);option.value=value;}
      input.value=draft.mapping[role]||"";input.addEventListener("change",()=>{draft.mapping[role]=input.value;});
    }
    const label=this._node("label",this._t("Legacy supply profile"),card);label.style.display="block";
    const profile=this._node("select",undefined,label);
    for(const value of draft.profiles){const option=this._node("option",value,profile);option.value=value;}
    profile.value=draft.profile;profile.addEventListener("change",()=>{draft.profile=profile.value;});
    this._field(card,this._t("Legacy price comparison end (exclusive date)"),draft.horizon,"date",v=>draft.horizon=v);
    this._field(card,this._t("Activate converted supply profile after import"),draft.activate,"checkbox",v=>draft.activate=v);
    if(draft.study_available)
      this._field(card,this._t("Continue the legacy study with its original report dates"),!!draft.resumeStudy,"checkbox",v=>draft.resumeStudy=v);
    this._field(card,this._t("I reviewed the mapping and confirm importing this backup"),draft.confirm,"checkbox",v=>draft.confirm=v);
    const submit=this._button(this._t("Import reviewed history"),card,async()=>{
      if(!draft.confirm || draft.roles.some(r=>!draft.mapping[r]) || !draft.horizon){this._error="Complete all mappings and the date, then confirm the review.";this._render();return;}
      if(draft.resumeStudy && !draft.activate){this._error="To continue the study, also activate the converted supply profile.";this._render();return;}
      submit.disabled=true;
      try{
        this._importResult=await this._api("POST","history",{command:"import",id:draft.id,sha256:draft.sha256,mapping:draft.mapping,horizon:draft.horizon,profile:draft.profile,activate:draft.activate,resume_study:!!draft.resumeStudy,confirm:true});
        this._importDraft=null;this._error=null;await this._refresh();
      }catch(_){this._error="Import failed. Possible reasons include overlap with native collection, previously imported history or invalid settings. Check the data; existing stores are not overwritten.";this._render();}
    });
    this._button(this._t("Discard uploaded backup"),card,async()=>{
      try{await this._api("POST","history",{command:"discard",id:draft.id});this._importDraft=null;this._error=null;this._render();}
      catch(_){this._error="Could not discard the uploaded backup.";this._render();}
    });
  }
  _settingsForm(card) {
    const active=this._profiles?.versions.find(v=>v.id===this._profiles.active)?.profile;
    if(!active){this._node("p",this._t("First create a price profile in the Profiles tab."),card);return;}
    const draft=this._settingsDraft || JSON.parse(JSON.stringify(active));
    const touch=()=>{this._settingsDraft=draft;};
    this._node("p",this._t("Changes create a new profile version. Frozen reports are preserved."),card);
    const ev=this._node("details",undefined,card);this._node("summary",this._t("EV calculation from counter increments"),ev);
    const enabled=this._field(ev,this._t("Use sample-level calculation"),!!draft.session,"checkbox",v=>{
      if(v)draft.session={max_gap_seconds:90,max_power_kw:null,tolerance_kwh:0,charging_kw:.1,charging_delta_kwh:0};else delete draft.session;
      touch();this._render();
    });enabled.setAttribute("aria-label",this._t("EV counter calculation"));
    if(draft.session) for(const [key,label] of [["max_gap_seconds",this._t("Maximum sample gap (s)")],["max_power_kw",this._t("Maximum EV power (kW)")],["tolerance_kwh",this._t("Counter increment tolerance (kWh)")],["charging_kw",this._t("Charging power threshold (kW)")],["charging_delta_kwh",this._t("Energy increment threshold (kWh)")]])
      this._field(ev,label,draft.session[key],"number",v=>{draft.session[key]=v===""?null:Number(v);touch();});
    this._node("small",this._t("Select EV mode sensors in source settings. The integration only records state and never controls the charger."),ev);
    const regional=this._node("details",undefined,card);this._node("summary",this._t("Network charges, levies and VAT"),regional);
    this._node("p",this._t("SI 2026 calendar. Enter effective rates excluding VAT and their validity periods. Enter rates with applicable reductions included. Blank means unknown. Connection power is not agreed block power."),regional);
    for(const [index,version] of (draft.regional || []).entries()) {
      const box=this._node("fieldset",undefined,regional);this._node("legend",this._t`Version ${index+1}`,box);
      for(const [key,label,type] of [["from",this._t("Valid from"),"date"],["until",this._t("Valid until (exclusive)"),"date"],["source",this._t("Rate source"),"text"],["confirmed",this._t("Rates checked against a valid contract/invoice"),"checkbox"]])
        this._field(box,label,version[key],type,v=>{version[key]=v;touch();});
      for(const block of ["1","2","3","4","5"])
        for(const [key,label] of [["energy",this._t("Energy EUR/kWh")],["power",this._t("Power EUR/kW/month")],["agreed_kw",this._t("Agreed power kW")]])
          this._field(box,this._t`Block ${block}: ${label}`,version[key][block],"number",v=>{version[key][block]=v===""?null:v;touch();});
      for(const [key,label] of [["vat",this._t("Import VAT (fraction, e.g. 0.22)")],["export_vat",this._t("Export VAT (fraction)")],["operator_kwh",this._t("Operator EUR/kWh")],["efficiency_kwh",this._t("Efficiency EUR/kWh")],["excise_kwh",this._t("Excise EUR/kWh")],["renewables_kw",this._t("Renewables/CHP basis (kW)")],["renewables_kw_month",this._t("Renewables/CHP EUR/kW/month")],["excess_factor",this._t("Excess-power factor")]])
        this._field(box,label,version[key],"number",v=>{version[key]=v===""?null:v;touch();});
      const exciseLabel=this._node("label",this._t("Excise basis"),box);
      const exciseSelect=this._node("select",undefined,exciseLabel);
      for(const [value,label] of [["import",this._t("Imported energy")],["net_import",this._t("Net imported energy over the billing period")]]) {
        const option=this._node("option",label,exciseSelect);
        option.value=value;
        option.selected=(version.excise_basis ?? "import")===value;
      }
      exciseSelect.addEventListener("change",()=>{version.excise_basis=exciseSelect.value;touch();});
      const label=this._node("label",this._t("Excess-power mode"),box),select=this._node("select",undefined,label);
      for(const [value,text] of [["unknown",this._t("Unconfirmed")],["informative",this._t("Informative, not charged")],["charged",this._t("Charged")]]){const option=this._node("option",text,select);option.value=value;option.selected=version.excess_mode===value;}
      select.addEventListener("change",()=>{version.excess_mode=select.value;touch();});
      this._button(this._t("Remove version from draft"),box,()=>{draft.regional.splice(index,1);if(!draft.regional.length)delete draft.regional;touch();this._render();});
    }
    this._button(this._t("Add rate period"),regional,()=>{
      const blank=()=>Object.fromEntries(["1","2","3","4","5"].map(k=>[k,null]));
      (draft.regional ||= []).push({from:"",until:"",source:"",confirmed:false,calendar:"si_2026",energy:blank(),power:blank(),agreed_kw:blank(),excess_mode:"unknown",
        vat:null,export_vat:null,operator_kwh:null,efficiency_kwh:null,excise_kwh:null,renewables_kw:null,renewables_kw_month:null,excess_factor:null});
      touch();this._render();
    });
    this._button(this._t("Save EV and billing"),card,async()=>{
      try{this._profiles=await this._api("POST","profiles",draft);this._settingsDraft=null;this._error=null;this._render();await this._refresh();}
      catch(_){this._error="Check all limits, effective dates and decimal rates. The draft is retained.";this._render();}
    });
    this._button(this._t("Discard setting changes"),card,()=>{this._settingsDraft=null;this._render();});
  }
  _studyForm(card) {
    const status=this._study || {state:"not_configured"};
    this._node("p",this._t`Study state: ${this._status(status.state)}`,card);
    if(status.quality)this._node("p",this._t`Warm-up coverage: ${this._number(status.quality.coverage*100,"%")} · daily check: ${this._status(status.quality.daily.status)}`,card);
    if(["warmup","running"].includes(status.state)) {
      this._node("small",this._t("After successful warm-up, the study starts at the next local midnight. Monthly and final reports are created automatically; the final summary does not duplicate session lists."),card);
      this._button(this._t("Stop study (keep reports)"),card,async()=>{try{this._study=await this._api("POST","study",{cancel:true});this._error=null;this._render();await this._refresh();}catch(_){this._error="Could not stop the study.";this._render();}});
      return;
    }
    const draft=this._studyDraft || {timezone:this._hass?.config?.time_zone || "Europe/Ljubljana",months:3,warmup_hours:48,minimum_coverage:.99,require_daily_check:true,daily_absolute_kwh:.1,daily_relative:.01,reference_age_seconds:180};
    for(const [key,label,type] of [["timezone",this._t("Time zone"),"text"],["months",this._t("Number of months"),"number"],["warmup_hours",this._t("Warm-up (hours)"),"number"],["minimum_coverage",this._t("Minimum coverage (fraction)"),"number"],["require_daily_check",this._t("Require daily comparison with household sensor"),"checkbox"],["daily_absolute_kwh",this._t("Daily absolute tolerance (kWh)"),"number"],["daily_relative",this._t("Daily relative tolerance (fraction)"),"number"],["reference_age_seconds",this._t("Maximum daily-reference age (s)"),"number"]])
      this._field(card,label,draft[key],type,v=>{draft[key]=type==="number"?Number(v):v;this._studyDraft=draft;});
    this._node("small",this._t("Select the household daily reference in integration sources. Warm-up cannot finish without a valid required reference."),card);
    this._button(this._t("Start study warm-up"),card,async()=>{try{this._study=await this._api("POST","study",draft);this._studyDraft=null;this._error=null;this._render();await this._refresh();}catch(_){this._error="Invalid study settings.";this._render();}});
    this._button(this._t("Discard study draft"),card,()=>{this._studyDraft=null;this._render();});
  }

  async _download(id, format) {
    try {
      const response=await this._hass.fetchWithAuth(`/api/energy_cost_monitor/report?id=${encodeURIComponent(id)}&format=${format}`);
      if(!response.ok)throw new Error("download");
      const url=URL.createObjectURL(await response.blob());
      const link=document.createElement("a");link.href=url;link.download=`energy-report.${format}`;link.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    } catch(_){this._error="Report download failed.";this._render();}
  }
}
if(!customElements.get("energy-cost-monitor-card"))customElements.define("energy-cost-monitor-card",EnergyCostMonitorCard);
window.customCards=window.customCards || [];
window.customCards.push({type:"energy-cost-monitor-card",name:"Energy Cost Monitor",description:"Supply scenarios, EV sessions and frozen reports"});

// Automatic admin sidebar uses the same bundled component; no YAML/resource edit.
class EnergyCostMonitorPanel extends EnergyCostMonitorCard {}
if(!customElements.get("energy-cost-monitor-panel"))customElements.define("energy-cost-monitor-panel",EnergyCostMonitorPanel);
