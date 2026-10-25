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
    this._timer = setInterval(() => this._refresh(), 30000);
    this._refresh();
  }
  disconnectedCallback() {
    this._connected = false; this._generation++; clearInterval(this._timer);
  }
  set hass(hass) { this._hass = hass; if (!this._data) this._refresh(); }
  async _api(method, action, data) {
    return this._hass.callApi(method, `energy_cost_monitor/${action}`, data);
  }
  async _refresh() {
    if (!this._connected || !this._hass || this._loading) return;
    if (this._tab === "profiles" && this._draft !== null) return;
    this._loading = true; const generation = this._generation;
    try {
      const end = Math.floor(Date.now()/900000)*900;
      const [data, profiles, reports] = await Promise.all([
        this._api("GET", `view?start=${end-this._days*86400}&end=${end}`), this._api("GET", "profiles"), this._api("GET", "reports")]);
      if (generation !== this._generation) return;
      this._data = data; this._profiles = profiles; this._reports = reports; this._error = null;
    } catch (_) { this._error = "Podatki niso dosegljivi. Potreben je skrbniški račun in naložena integracija."; }
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
  _number(value, unit="") { return value === null || value === undefined ? "neznano" : `${Number(value).toLocaleString("sl-SI", {maximumFractionDigits: 3})} ${unit}`; }
  _time(value) { return value === null || value === undefined ? "še odprta" : new Date(value*1000).toLocaleString("sl-SI"); }
  _render() {
    const root = this.shadowRoot; root.replaceChildren();
    const style = this._node("style", undefined, root);
    style.textContent = `:host{display:block}ha-card{padding:20px;color:var(--primary-text-color);font-family:var(--paper-font-body1_-_font-family,system-ui)}h2{margin:0 0 6px}nav{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}button{cursor:pointer;padding:9px 12px;border-radius:8px;border:1px solid var(--divider-color,#bbb);background:var(--card-background-color,#fff);color:inherit}button[aria-current=true]{background:var(--primary-color,#176b68);color:white}p{line-height:1.5}.muted{color:var(--secondary-text-color)}.error{color:var(--error-color,#b00020)}article{padding:12px 0;border-top:1px solid var(--divider-color,#ddd)}textarea{box-sizing:border-box;width:100%;min-height:180px;font:12px monospace;color:inherit;background:var(--secondary-background-color,#f5f5f5);border:1px solid var(--divider-color,#bbb);padding:10px}small{display:block;line-height:1.5} .actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}`;
    const card = this._node("ha-card", undefined, root);
    this._node("h2", this._config?.title || "Energy Cost Monitor", card);
    this._node("small", "Razvojni prikaz · dobavni stroški brez DDV, omrežnine in dajatev", card, "muted");
    const periods = this._node("div", undefined, card, "actions");
    for (const days of [1,7,30]) {
      const button = this._button(`${days} dni`, periods, ()=>{this._days=days;this._refresh();});
      button.setAttribute("aria-current",String(this._days===days));
    }
    const nav = this._node("nav", undefined, card);
    for (const [tab,label] of [["overview","Pregled"],["sessions","EV seje"],["reports","Poročila"],["profiles","Profili"]]) {
      const button = this._button(label,nav,()=>{this._tab=tab;this._render();});
      button.setAttribute("aria-current",String(this._tab===tab));
    }
    if(this._error) this._node("p",this._error,card,"error");
    if(!this._data){this._node("p","Čakam na podatke …",card);return;}
    const data=this._data;
    if(this._tab==="overview") {
      this._node("p",`Obdobje: ${this._time(data.start)} – ${this._time(data.end)}`,card);
      this._node("small",`Zadnji vzorec: ${this._time(data.latest_sample)}`,card,"muted");
      if(data.price_error) this._node("p","Cenovni vir trenutno ni dosegljiv. Meritve se zbirajo naprej.",card,"error");
      if(!data.comparison) this._node("p","Dodaj profil dobavnih scenarijev za primerjavo stroškov.",card);
      for(const result of data.comparison?.results || []) {
        const row=this._node("article",undefined,card);
        this._node("strong",result.scenario.identifier,row);
        this._node("p",`${this._number(result.total,"EUR")} · pokritost ${this._number(result.coverage*100,"%")}`,row);
        this._node("small",`Znani del: ${this._number(result.known_net_subtotal,"EUR")} · ${result.confirmed?"potrjene dobavne postavke":"referenčni ali nepopolni podatki"}`,row,"muted");
      }
      if(data.comparison) this._node("p",`Skupna pokritost ponudb: ${this._number(data.comparison.common_coverage*100,"%")}`,card);
      for(const source of Object.values(data.market_provenance || {})) this._node("small",`${source.source} · ${source.license}`,card,"muted");
      this._node("small","Energy-Charts.info: referenčni indeks; ujemanje z dobaviteljevim računom ni potrjeno.",card,"muted");
    } else if(this._tab==="sessions") {
      if(!data.sessions.length)this._node("p","V izbranem obdobju ni zaznanih EV sej.",card);
      for(const session of [...data.sessions].reverse()) {
        const row=this._node("article",undefined,card), body=session.body;
        this._node("strong",`${this._time(session.start)} → ${this._time(session.end)}`,row);
        this._node("p",`${this._number(body.kwh,"kWh")} · polnjenje ${this._number(body.charging_seconds/60,"min")} · premor ${this._number(body.pause_seconds/60,"min")}`,row);
        this._node("small",body.partial?"Delna seja: vrzeli ali neuvrščena energija na robovih intervalov.":"Pokriti intervali seje.",row,"muted");
      }
    } else if(this._tab==="reports") {
      this._node("p","Zamrznjeno poročilo ohrani podatke, profil in cenovne predpostavke trenutka izdelave.",card);
      this._button("Zamrzni prikazano obdobje",card,async()=>{
        try{await this._api("POST","reports",{start:data.start,end:data.end});await this._refresh();}
        catch(_){this._error="Poročila ni bilo mogoče shraniti.";this._render();}
      });
      for(const report of this._reports || []) {
        const row=this._node("article",undefined,card);
        this._node("strong",`${this._time(report.start)} – ${this._time(report.end)}`,row);
        const actions=this._node("div",undefined,row,"actions");
        for(const format of ["html","csv"])this._button(format.toUpperCase(),actions,()=>this._download(report.id,format));
      }
    } else {
      const form=this._node("details",undefined,card);
      this._node("summary","Nov enostaven cenovni profil",form);
      const fields={};
      for(const [key,label,type] of [["name","Ime profila","text"],["from","Velja od (UTC)","date"],["until","Velja do (UTC, izključno)","date"],["price","Uvoz EUR/kWh brez DDV","number"],["export","Oddaja EUR/kWh brez DDV","number"],["fee","Naročnina EUR/mesec brez DDV","number"]]) {
        const wrapper=this._node("label",label,form); wrapper.style.display="block";
        const input=this._node("input",undefined,wrapper);input.type=type;
        if(type==="number")input.step="any"; fields[key]=input;
      }
      this._node("small","Prazna cena pomeni neznano. Za ničelno naročnino vnesi 0. Cene so referenčne do preverjanja pogodbe.",form,"muted");
      this._button("Pripravi profil",form,()=>{
        const first=fields.from.value+"T00:00:00Z",last=fields.until.value+"T00:00:00Z";
        if(!fields.name.value.trim() || !Number.isFinite(Date.parse(first)) || Date.parse(last)<=Date.parse(first) || !Number.isFinite(Date.parse(last))) {
          this._error="Vnesi ime in veljavno obdobje.";this._render();return;
        }
        const quote=(value,unit)=>({value:value===""?null:value,unit,source:"Uporabniški vnos",status:value===""?"unknown":"reference"});
        const period=value=>({...quote(value,"EUR/kWh"),from:first,until:last});
        this._draft=JSON.stringify({name:fields.name.value,scenarios:[{schema_version:1,id:"my-offer",currency:"EUR",tax_basis:"excluding_vat",timezone:"UTC",versions:[{id:"version-1",from:first,until:last,import:[period(fields.price.value)],export:[period(fields.export.value)],subscription:quote(fields.fee.value,"EUR/month")}]}],indexed_import:{}},null,2);
        this._error=null;this._render();
      });
      this._node("p","Uvozi JSON profil z datumi veljavnosti, cenami in viri. Sprememba ustvari novo različico; poročila ostanejo nespremenjena.",card);
      const advanced=this._node("details",undefined,card);advanced.open=this._draft!==null;
      this._node("summary","Napredne nastavitve in predogled profila",advanced);
      const editor=this._node("textarea",undefined,advanced);editor.setAttribute("aria-label","JSON profil dobavnih scenarijev");
      const active=this._profiles?.versions.find(v=>v.id===this._profiles.active);
      editor.value=this._draft ?? JSON.stringify(active?.profile || {name:"Moj profil",scenarios:[],indexed_import:{}},null,2);
      editor.addEventListener("input",()=>{this._draft=editor.value;});
      this._button("Shrani novo različico",advanced,async()=>{
        try{await this._api("POST","profiles",JSON.parse(editor.value)); this._draft=null; await this._refresh();}
        catch(_){this._error="Profil ni veljaven ali shranjevanje ni uspelo.";this._render();}
      });
      this._button("Zavrzi osnutek",advanced,()=>{this._draft=null;this._render();});
      for(const version of this._profiles?.versions || []) {
        const row=this._node("article",undefined,card);
        this._node("strong",`${version.profile.name}${version.id===this._profiles.active?" · aktivna":""}`,row);
        if(version.id!==this._profiles.active)this._button("Uporabi to različico",row,async()=>{
          try{await this._api("POST","profiles",{activate:version.id});await this._refresh();}
          catch(_){this._error="Aktivacija profila ni uspela.";this._render();}
        });
      }
    }
  }
  async _download(id, format) {
    try {
      const response=await this._hass.fetchWithAuth(`/api/energy_cost_monitor/report?id=${encodeURIComponent(id)}&format=${format}`);
      if(!response.ok)throw new Error("download");
      const url=URL.createObjectURL(await response.blob());
      const link=document.createElement("a");link.href=url;link.download=`energy-report.${format}`;link.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    } catch(_){this._error="Prenos poročila ni uspel.";this._render();}
  }
}
if(!customElements.get("energy-cost-monitor-card"))customElements.define("energy-cost-monitor-card",EnergyCostMonitorCard);
window.customCards=window.customCards || [];
window.customCards.push({type:"energy-cost-monitor-card",name:"Energy Cost Monitor",description:"Dobavni scenariji, EV seje in zamrznjena poročila"});
