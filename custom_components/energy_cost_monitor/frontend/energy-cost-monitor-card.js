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
    if ((this._tab === "profiles" && this._draft !== null) || this._importDraft || this._pricingDraft || this._settingsDraft || this._studyDraft) return;
    this._loading = true; const generation = this._generation;
    try {
      const end = Math.floor(Date.now()/900000)*900;
      const [data, profiles, reports, study] = await Promise.all([
        this._api("GET", `view?start=${end-this._days*86400}&end=${end}`), this._api("GET", "profiles"), this._api("GET", "reports"), this._api("GET", "study")]);
      if (generation !== this._generation) return;
      this._data = data; this._profiles = profiles; this._reports = reports; this._study = study; this._error = null;
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
    this._node("small", "Dobavni stroški in ločena regionalna ocena · ni račun ali znesek za plačilo", card, "muted");
    const periods = this._node("div", undefined, card, "actions");
    for (const days of [1,7,30]) {
      const button = this._button(`${days} dni`, periods, ()=>{this._days=days;this._refresh();});
      button.setAttribute("aria-current",String(this._days===days));
    }
    const nav = this._node("nav", undefined, card);
    for (const [tab,label] of [["overview","Pregled"],["sessions","EV seje"],["reports","Poročila"],["profiles","Profili"],["pricing","Cene"],["settings","EV in obračun"],["study","Študija"],["history","Uvoz zgodovine"]]) {
      const button = this._button(label,nav,()=>{this._tab=tab;this._render();});
      button.setAttribute("aria-current",String(this._tab===tab));
    }
    if(this._error) this._node("p",this._error,card,"error");
    if(!this._data){this._node("p","Čakam na podatke …",card);return;}
    const data=this._data;
    if(this._tab==="history") { this._historyForm(card);
    } else if(this._tab==="pricing") { this._pricingForm(card);
    } else if(this._tab==="settings") { this._settingsForm(card);
    } else if(this._tab==="study") { this._studyForm(card);
    } else if(this._tab==="overview") {
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
      for(const [name,bill] of Object.entries(data.regional_bills || {})) {
        const row=this._node("article",undefined,card);
        this._node("strong",`${name} · regionalna ocena`,row);
        this._node("p",`Celota: ${this._number(bill.total_gross,"EUR")} · znani del: ${this._number(bill.known_reference_gross,"EUR")}`,row);
        for(const [key,value] of Object.entries(bill.components))this._node("small",`${key}: ${this._number(value,"EUR")}`,row);
        this._node("small",bill.missing.length?`Manjka: ${bill.missing.join(", ")}`:"Ocena po HA meritvah, ne znesek za plačilo.",row,"muted");
      }
      if(data.comparison) this._node("p",`Skupna pokritost ponudb: ${this._number(data.comparison.common_coverage*100,"%")}`,card);
      for(const source of Object.values(data.market_provenance || {})) this._node("small",`${source.source} · ${source.license}`,card,"muted");
      this._node("small","Energy-Charts.info: referenčni indeks; ujemanje z dobaviteljevim računom ni potrjeno.",card,"muted");
    } else if(this._tab==="sessions") {
      if(!data.sessions.length)this._node("p","V izbranem obdobju ni zaznanih EV sej.",card);
      for(const session of [...data.sessions].reverse()) {
        const row=this._node("article",undefined,card), body=session.body;
        if(session.legacy)this._node("small","Arhivirana seja stare aplikacije · prvotni izračun",row,"muted");
        this._node("strong",`${this._time(session.start)} → ${this._time(session.end)}`,row);
        this._node("p",`${this._number(body.kwh,"kWh")} · polnjenje ${this._number(body.charging_seconds/60,"min")} · premor ${this._number(body.pause_seconds/60,"min")}`,row);
        for(const [name,total] of Object.entries(body.mode_totals || {}))this._node("small",`${name}: ${this._number(total.kwh,"kWh")} · ${this._number(total.seconds/60,"min")}`,row);
        const events=this._node("details",undefined,row);this._node("summary","Dogodki in načini (samo opazovanje)",events);
        for(const event of body.events || [])this._node("small",`${this._time(event.ts)} · ${event.state} · ${Object.entries(event.mode || {}).filter(([,v])=>v!==null).map(([k,v])=>`${k}: ${v}`).join(" · ")}`,events);
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
        if(report.legacy)this._node("small","Arhivirano poročilo · brez ponovnega izračuna",row,"muted");
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
    const quote=(unit)=>({value:null,unit,source:"Uporabniški vnos",status:"unknown"});
    const priceFields=(parent,p,monthly=false)=>{
      this._field(parent,monthly?"Naročnina po popustu (EUR/mesec brez DDV)":"Cena brez DDV",p.value,"number",v=>{
        p.value=v===""?null:v;p.status=p.value===null?"unknown":p.status==="unknown"?"reference":p.status;touch();
      });
      if(!monthly)select(parent,"Enota",p.unit,[["EUR/kWh","EUR/kWh"],["EUR/MWh","EUR/MWh"]],v=>p.unit=v);
      field(parent,"Vir cene",p,"source");
      this._field(parent,"Potrjeno s pogodbo oziroma računom",p.status==="confirmed","checkbox",v=>{
        p.status=p.value===null?"unknown":v?"confirmed":"reference";touch();
      });
    };
    this._node("p","Uredi ponudbe in obdobja prek obrazcev. Prazne cene ostanejo neznane. Časi veljavnosti morajo vsebovati časovni odmik, npr. 2026-01-01T00:00:00+01:00; konec je izključen. Spremembe shranijo novo različico.",card);
    field(card,"Ime profila",draft,"name");
    for(const scenario of draft.scenarios){
      const box=this._node("fieldset",undefined,card);this._node("legend",scenario.id,box);
      field(box,"Časovni pas (IANA)",scenario,"timezone");
      this._node("small","Identifikator ponudbe: "+scenario.id,box);
      select(box,"Cena prevzema",draft.indexed_import[scenario.id]?"indexed":"fixed",[["fixed","Vnesene cene"],["indexed","Referenčni indeks Energy-Charts + pribitek"]],v=>{
        if(v==="indexed")draft.indexed_import[scenario.id]={zone:"SI",markup_eur_kwh:"0"};else delete draft.indexed_import[scenario.id];
      }).addEventListener("change",()=>this._render());
      const binding=draft.indexed_import[scenario.id];
      if(binding){
        select(box,"Območje indeksa",binding.zone,["SI","AT","DE-LU","HR","IT-North","HU"].map(v=>[v,v]),v=>binding.zone=v);
        field(box,"Pribitek EUR/kWh",binding,"markup_eur_kwh","number");
        this._node("small","Indeks nadomesti vnesene cene prevzema znotraj veljavnosti pogodb. Gre za referenco, ne potrjeno dobaviteljevo formulo.",box);
      }
      for(const version of scenario.versions){
        const group=this._node("fieldset",undefined,box);this._node("legend",version.id,group);
        field(group,"Veljavnost od",version,"from");field(group,"Veljavnost do",version,"until");
        priceFields(group,version.subscription,true);
        for(const [direction,label] of [["import","Prevzem"],["export","Oddaja"]]){
          const section=this._node("details",undefined,group);this._node("summary",label,section);
          for(const period of version[direction]){
            const row=this._node("fieldset",undefined,section);
            field(row,"Cena velja od",period,"from");field(row,"Cena velja do",period,"until");priceFields(row,period);
            this._button("Odstrani cenovno obdobje",row,()=>{version[direction].splice(version[direction].indexOf(period),1);touch();this._render();});
          }
          this._button("Dodaj obdobje: "+label,section,()=>{version[direction].push({...quote("EUR/kWh"),from:version.from,until:version.until});touch();this._render();});
        }
        this._button("Odstrani različico pogodbe",group,()=>{scenario.versions.splice(scenario.versions.indexOf(version),1);touch();this._render();});
      }
      this._button("Dodaj različico pogodbe",box,()=>{
        let n=1;while(scenario.versions.some(v=>v.id===`version-${n}`))n++;
        scenario.versions.push({id:`version-${n}`,from:"",until:"",import:[],export:[],subscription:quote("EUR/month")});touch();this._render();
      });
      this._button("Odstrani ponudbo",box,()=>{draft.scenarios.splice(draft.scenarios.indexOf(scenario),1);delete draft.indexed_import[scenario.id];touch();this._render();});
    }
    this._button("Dodaj ponudbo",card,()=>{
      let n=1;while(draft.scenarios.some(s=>s.id===`offer-${n}`))n++;
      draft.scenarios.push({schema_version:1,id:`offer-${n}`,currency:"EUR",tax_basis:"excluding_vat",timezone:this._hass?.config?.time_zone || "UTC",versions:[]});touch();this._render();
    });
    this._button("Shrani cenovni profil",card,async()=>{
      touch();try{await this._api("POST","profiles",draft);this._pricingDraft=null;this._error=null;await this._refresh();}
      catch(_){this._error="Preveri ime, veljavnost, cene in prekrivanje obdobij. Osnutek je ohranjen.";this._render();}
    });
    this._button("Zavrzi cenovne spremembe",card,()=>{this._pricingDraft=null;this._error=null;this._render();});
  }
  _historyForm(card) {
    this._node("p","Izberi konsistentno kopijo SQLite starega Energy Cost Monitorja. Datoteka se naloži samo v tvoj HA. Uvoz ohrani originalne zapise in doda zgodovino pred začetkom novih meritev; prekrivanje je zavrnjeno. Pred zapisom se zasebno shranita kopiji obeh trenutnih zbirk.",card);
    this._node("small","Uvoz prenese meritve, dobavne profile ter arhiv sej in poročil. Stara študija in regionalne nastavitve se ne aktivirajo samodejno. Obnova celotnega HA še vedno uporablja njegove varnostne kopije.",card);
    if(this._importResult)this._node("p",`Uvoz uspešen: ${this._importResult.converted_role_intervals} merilnih zapisov, ${this._importResult.profiles} profilov, ${this._importResult.reports} poročil. Kopija pred uvozom: ${this._importResult.backup}`,card);
    if(!this._importDraft){
      this._button("Prikaži že naložene kopije",card,async()=>{
        try{this._uploads=await this._api("GET","history");this._render();}
        catch(_){this._error="Seznam ni dosegljiv.";this._render();}
      });
      for(const pending of this._uploads || []){
        const row=this._node("article",`Naloženo: ${this._time(pending.created)}`,card);
        this._button("Nadaljuj pregled kopije",row,async()=>{
          try{const preview=await this._api("POST","history",{command:"resume",id:pending.id});this._importDraft={...preview,mapping:{},horizon:"",profile:preview.profiles[0],activate:false,confirm:false};this._render();}
          catch(_){this._error="Kopija ni dosegljiva.";this._render();}
        });
        this._button("Odstrani naloženo kopijo",row,async()=>{
          try{await this._api("POST","history",{command:"discard",id:pending.id});this._uploads=this._uploads.filter(x=>x.id!==pending.id);this._render();}
          catch(_){this._error="Kopije ni bilo mogoče odstraniti.";this._render();}
        });
      }
      const label=this._node("label","Kopija stare zbirke (.sqlite3)",card);
      const file=this._node("input",undefined,label);file.type="file";file.accept=".sqlite3,.sqlite,.db";
      const upload=this._button("Naloži in preglej kopijo",card,async()=>{
        if(!file.files?.length){this._error="Izberi datoteko kopije.";this._render();return;}
        upload.disabled=true;
        try{
          const body=new FormData();body.append("file",file.files[0]);
          const response=await this._hass.fetchWithAuth("/api/file_upload",{method:"POST",body});
          if(!response.ok)throw Error("upload_failed");
          const uploaded=await response.json();
          const preview=await this._api("POST","history",{command:"preview",file_id:uploaded.file_id});
          this._importDraft={...preview,mapping:{},horizon:"",profile:preview.profiles[0],activate:false,confirm:false};this._error=null;
        }catch(_){this._error="Kopije ni bilo mogoče preveriti. Uporabi podprto konsistentno zbirko do 100 MB.";}
        this._render();
      });return;
    }
    const draft=this._importDraft;
    this._node("p",`Pregled: ${draft.counts.intervals} starih intervalov, ${draft.counts.sessions} sej. Meja zgodovine: ${this._time(draft.cutover)}.`,card);
    for(const role of draft.roles){
      const label=this._node("label",`Stara meritev za ${role}`,card);label.style.display="block";
      const input=this._node("select",undefined,label);
      for(const value of ["",...draft.metrics]){const option=this._node("option",value||"Izberi meritev",input);option.value=value;}
      input.value=draft.mapping[role]||"";input.addEventListener("change",()=>{draft.mapping[role]=input.value;});
    }
    const label=this._node("label","Stari dobavni profil",card);label.style.display="block";
    const profile=this._node("select",undefined,label);
    for(const value of draft.profiles){const option=this._node("option",value,profile);option.value=value;}
    profile.value=draft.profile;profile.addEventListener("change",()=>{draft.profile=profile.value;});
    this._field(card,"Konec primerjave starih cen (izključni datum)",draft.horizon,"date",v=>draft.horizon=v);
    this._field(card,"Po uvozu aktiviraj pretvorjeni dobavni profil",draft.activate,"checkbox",v=>draft.activate=v);
    this._field(card,"Pregledal sem preslikavo in potrjujem uvoz te kopije",draft.confirm,"checkbox",v=>draft.confirm=v);
    const submit=this._button("Uvozi preverjeno zgodovino",card,async()=>{
      if(!draft.confirm || draft.roles.some(r=>!draft.mapping[r]) || !draft.horizon){this._error="Izpolni vse preslikave in datum ter potrdi pregled.";this._render();return;}
      submit.disabled=true;
      try{
        this._importResult=await this._api("POST","history",{command:"import",id:draft.id,sha256:draft.sha256,mapping:draft.mapping,horizon:draft.horizon,profile:draft.profile,activate:draft.activate,confirm:true});
        this._importDraft=null;this._error=null;await this._refresh();
      }catch(_){this._error="Uvoz ni uspel. Možni razlogi so prekrivanje z novimi meritvami, že uvožena zgodovina ali napačne nastavitve. Preveri podatke; obstoječe zbirke se ne prepisujejo.";this._render();}
    });
    this._button("Zavrzi naloženo kopijo",card,async()=>{
      try{await this._api("POST","history",{command:"discard",id:draft.id});this._importDraft=null;this._error=null;this._render();}
      catch(_){this._error="Naložene kopije ni bilo mogoče zavreči.";this._render();}
    });
  }
  _settingsForm(card) {
    const active=this._profiles?.versions.find(v=>v.id===this._profiles.active)?.profile;
    if(!active){this._node("p","Najprej ustvari cenovni profil v zavihku Profili.",card);return;}
    const draft=this._settingsDraft || JSON.parse(JSON.stringify(active));
    const touch=()=>{this._settingsDraft=draft;};
    this._node("p","Spremembe ustvarijo novo različico profila. Zamrznjena poročila ostanejo ohranjena.",card);
    const ev=this._node("details",undefined,card);this._node("summary","EV izračun iz prirastkov števca",ev);
    const enabled=this._field(ev,"Uporabi izračun na ravni vzorcev",!!draft.session,"checkbox",v=>{
      if(v)draft.session={max_gap_seconds:90,max_power_kw:null,tolerance_kwh:0,charging_kw:.1,charging_delta_kwh:0};else delete draft.session;
      touch();this._render();
    });enabled.setAttribute("aria-label","Izračun EV iz števca");
    if(draft.session) for(const [key,label] of [["max_gap_seconds","Največji razmik vzorcev (s)"],["max_power_kw","Največja moč EV (kW)"],["tolerance_kwh","Toleranca koraka števca (kWh)"],["charging_kw","Prag moči polnjenja (kW)"],["charging_delta_kwh","Prag energijskega prirastka (kWh)"]])
      this._field(ev,label,draft.session[key],"number",v=>{draft.session[key]=v===""?null:Number(v);touch();});
    this._node("small","Senzorje načinov EV izberi v nastavitvah virov. Integracija samo beleži stanje in nikoli ne upravlja polnilnice.",ev);
    const regional=this._node("details",undefined,card);this._node("summary","Omrežnina, dajatve in DDV",regional);
    this._node("p","Koledar SI 2026. Vnesi veljavne postavke brez DDV in pripadajoča obdobja. Znižanja vključuje vnesena tarifa. Prazno pomeni neznano. Priključna moč ni dogovorjena moč po blokih.",regional);
    for(const [index,version] of (draft.regional || []).entries()) {
      const box=this._node("fieldset",undefined,regional);this._node("legend",`Različica ${index+1}`,box);
      for(const [key,label,type] of [["from","Velja od","date"],["until","Velja do (izključno)","date"],["source","Vir postavk","text"],["confirmed","Postavke preverjene z veljavno pogodbo/računom","checkbox"]])
        this._field(box,label,version[key],type,v=>{version[key]=v;touch();});
      for(const block of ["1","2","3","4","5"])
        for(const [key,label] of [["energy","Energija EUR/kWh"],["power","Moč EUR/kW/mesec"],["agreed_kw","Dogovorjena moč kW"]])
          this._field(box,`ČB${block}: ${label}`,version[key][block],"number",v=>{version[key][block]=v===""?null:v;touch();});
      for(const [key,label] of [["vat","DDV prevzem (delež, npr. 0,22)"],["export_vat","DDV odkup (delež)"],["operator_kwh","Operater EUR/kWh"],["efficiency_kwh","Učinkovitost EUR/kWh"],["excise_kwh","Trošarina EUR/kWh"],["renewables_kw","Osnova OVE/SPTE (kW)"],["renewables_kw_month","OVE/SPTE EUR/kW/mesec"],["excess_factor","Faktor presežne moči"]])
        this._field(box,label,version[key],"number",v=>{version[key]=v===""?null:v;touch();});
      const label=this._node("label","Režim presežne moči",box),select=this._node("select",undefined,label);
      for(const [value,text] of [["unknown","Ni potrjeno"],["informative","Informativno, brez zaračunavanja"],["charged","Zaračunano"]]){const option=this._node("option",text,select);option.value=value;option.selected=version.excess_mode===value;}
      select.addEventListener("change",()=>{version.excess_mode=select.value;touch();});
      this._button("Odstrani različico iz osnutka",box,()=>{draft.regional.splice(index,1);if(!draft.regional.length)delete draft.regional;touch();this._render();});
    }
    this._button("Dodaj obdobje postavk",regional,()=>{
      const blank=()=>Object.fromEntries(["1","2","3","4","5"].map(k=>[k,null]));
      (draft.regional ||= []).push({from:"",until:"",source:"",confirmed:false,calendar:"si_2026",energy:blank(),power:blank(),agreed_kw:blank(),excess_mode:"unknown",
        vat:null,export_vat:null,operator_kwh:null,efficiency_kwh:null,excise_kwh:null,renewables_kw:null,renewables_kw_month:null,excess_factor:null});
      touch();this._render();
    });
    this._button("Shrani EV in obračun",card,async()=>{
      try{await this._api("POST","profiles",draft);this._settingsDraft=null;await this._refresh();}
      catch(_){this._error="Preveri vse meje, datume veljavnosti in decimalne postavke. Osnutek ostaja ohranjen.";this._render();}
    });
    this._button("Zavrzi spremembe nastavitev",card,()=>{this._settingsDraft=null;this._render();});
  }
  _studyForm(card) {
    const status=this._study || {state:"not_configured"};
    this._node("p",`Stanje študije: ${status.state}`,card);
    if(status.quality)this._node("p",`Pokritost uvajanja: ${this._number(status.quality.coverage*100,"%")} · dnevna kontrola: ${status.quality.daily.status}`,card);
    if(["warmup","running"].includes(status.state)) {
      this._node("small","Začetek se določi po uspešnem uvajanju ob naslednji lokalni polnoči. Mesečna in končno poročilo se ustvarijo samodejno; končni zbirni pregled brez podvajanja seznamov sej.",card);
      this._button("Ustavi študijo (ohrani poročila)",card,async()=>{try{await this._api("POST","study",{cancel:true});await this._refresh();}catch(_){this._error="Študije ni bilo mogoče ustaviti.";this._render();}});
      return;
    }
    const draft=this._studyDraft || {timezone:this._hass?.config?.time_zone || "Europe/Ljubljana",months:3,warmup_hours:48,minimum_coverage:.99,require_daily_check:true,daily_absolute_kwh:.1,daily_relative:.01,reference_age_seconds:180};
    for(const [key,label,type] of [["timezone","Časovni pas","text"],["months","Število mesecev","number"],["warmup_hours","Uvajanje (ure)","number"],["minimum_coverage","Najmanjša pokritost (delež)","number"],["require_daily_check","Zahtevaj dnevno primerjavo s senzorjem hiše","checkbox"],["daily_absolute_kwh","Dnevna absolutna toleranca (kWh)","number"],["daily_relative","Dnevna relativna toleranca (delež)","number"],["reference_age_seconds","Največja starost dnevne reference (s)","number"]])
      this._field(card,label,draft[key],type,v=>{draft[key]=type==="number"?Number(v):v;this._studyDraft=draft;});
    this._node("small","Dnevno referenco hiše izberi v virih integracije. Brez zahtevane veljavne reference se uvajanje ne zaključi.",card);
    this._button("Začni uvajanje študije",card,async()=>{try{await this._api("POST","study",draft);this._studyDraft=null;await this._refresh();}catch(_){this._error="Nastavitve študije niso veljavne.";this._render();}});
    this._button("Zavrzi osnutek študije",card,()=>{this._studyDraft=null;this._render();});
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

// Automatic admin sidebar uses the same bundled component; no YAML/resource edit.
class EnergyCostMonitorPanel extends EnergyCostMonitorCard {}
if(!customElements.get("energy-cost-monitor-panel"))customElements.define("energy-cost-monitor-panel",EnergyCostMonitorPanel);
