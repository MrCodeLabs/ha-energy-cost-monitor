// Behavioral card tests with a minimal DOM double; not a browser/HA frontend test.
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
class Element {
  constructor(tag) { this.tag=tag; this.children=[]; this.events={}; this.attrs={}; this.style={}; }
  append(child) { this.children.push(child); child.parent=this; }
  querySelectorAll(selector) { return this.children.flatMap(child=>[...(selector.split(",").includes(child.tag)?[child]:[]),...child.querySelectorAll(selector)]); }
  querySelector(selector) { return this.querySelectorAll(selector)[0]; }
  replaceWith(node) { const i=this.parent.children.indexOf(this); this.parent.children[i]=node; node.parent=this.parent; }
  replaceChildren() { this.children=[]; }
  addEventListener(name,callback) { this.events[name]=callback; }
  setAttribute(name,value) { this.attrs[name]=value; }
  attachShadow() { return this.shadowRoot=new Element('shadow'); }
}
let Card;
const context={HTMLElement:Element,document:{createElement:tag=>new Element(tag)},
  customElements:{get:()=>undefined,define:(_,value)=>{Card=value;}},window:{},
  setInterval:()=>1,clearInterval:()=>{},setTimeout:()=>{},URL,Date,console};
vm.runInNewContext(readFileSync('custom_components/energy_cost_monitor/frontend/energy-cost-monitor-card.js','utf8'),context);
const nodes=(root,tag)=>[...(root.tag===tag?[root]:[]),...root.children.flatMap(n=>nodes(n,tag))];
const data={start:0,end:900,sessions:[],comparison:null,latest_sample:null};
const profiles={active:null,versions:[]};
(async()=>{
  const card=new Card();card.setConfig({});card._connected=true;
  let calls=0;
  card._hass={callApi:async(method,action)=>{calls++;return action.includes('/view')?data:action.endsWith('/profiles')?profiles:[];}};
  await card._refresh();assert.equal(calls,4);assert.equal(card._data,data);
  for(const tab of ['pricing','settings','history','study']) {
    card._tab=tab;await card._poll();assert.equal(calls,4,'timer must preserve open forms');
  }
  card._tab='profiles';card._render();
  let editor=nodes(card.shadowRoot,'textarea')[0];editor.value='unfinished profile';editor.events.input();
  await card._refresh();assert.equal(calls,4,'refresh must not discard edits');
  card._render();assert.equal(nodes(card.shadowRoot,'textarea')[0].value,'unfinished profile');
  const discard=nodes(card.shadowRoot,'button').find(n=>n.textContent==='Discard draft');discard.events.click();assert.equal(card._draft,null);
  card._config.title='<img src=x onerror=alert(1)>';card._render();assert.equal(nodes(card.shadowRoot,'h2')[0].textContent,card._config.title);assert.equal(nodes(card.shadowRoot,'img').length,0);
  card._tab='overview';let release;
  card._hass.callApi=()=>new Promise(resolve=>{release=resolve;});
  // Use one deferred promise for all three API requests.
  const pending=new Promise(resolve=>{release=resolve;});card._hass.callApi=()=>pending;
  const refresh=card._refresh();card.disconnectedCallback();release([]);await refresh;
  assert.equal(card._data,data,'disconnected request must not replace state');
  const formCard=new Card();formCard._data=data;formCard._profiles=profiles;formCard._tab='profiles';formCard._render();
  const inputs=nodes(formCard.shadowRoot,'input');
  ['Example','2026-01-01','2027-01-01','0.2','','0'].forEach((value,index)=>inputs[index].value=value);
  nodes(formCard.shadowRoot,'button').find(n=>n.textContent==='Prepare profile').events.click();
  const profile=JSON.parse(formCard._draft);assert.equal(profile.scenarios[0].versions[0].export[0].value,null);
  assert.equal(profile.scenarios[0].versions[0].subscription.value,'0');
  formCard._profiles={active:'example',versions:[{id:'example',profile}]};
  formCard._tab='pricing';formCard._render();
  let nameInput=nodes(formCard.shadowRoot,'input')[0];nameInput.value='Changed';nameInput.events.input();
  formCard._render();assert.equal(nodes(formCard.shadowRoot,'input')[0].value,'Changed');
  assert.equal(profile.name,'Example','editing must not mutate saved profile');
  nodes(formCard.shadowRoot,'button').find(n=>n.textContent==='Add offer').events.click();
  assert.equal(formCard._pricingDraft.scenarios.length,2);
  let saved;
  const savedProfiles={active:'saved',versions:[{id:'saved',profile}]};
  formCard._hass={callApi:async(method,action,payload)=>{saved=payload;return savedProfiles;}};
  await nodes(formCard.shadowRoot,'button').find(n=>n.textContent==='Save price profile').events.click();
  assert.equal(saved.name,'Changed');assert.equal(formCard._pricingDraft,null);
  assert.equal(formCard._profiles,savedProfiles,'save response must update visible profile even when refresh is blocked');
  formCard._render();nameInput=nodes(formCard.shadowRoot,'input')[0];nameInput.value='Retained';nameInput.events.input();
  formCard._hass.callApi=async()=>{throw Error('offline');};
  await nodes(formCard.shadowRoot,'button').find(n=>n.textContent==='Save price profile').events.click();
  assert.equal(formCard._pricingDraft.name,'Retained');
  formCard._tab='study';formCard._study={state:'not_configured'};formCard._render();
  formCard._hass.callApi=async()=>({state:'warmup'});
  await nodes(formCard.shadowRoot,'button').find(n=>n.textContent==='Start study warm-up').events.click();
  assert.equal(formCard._study.state,'warmup');
  assert(nodes(formCard.shadowRoot,'p').some(n=>n.textContent==='Study state: Warm-up'));
  formCard._tab='sessions';formCard._data={...data,sessions:[{legacy:true,start:0,end:900,body:{kwh:1,charging_seconds:60,pause_seconds:10,partial:true}}]};formCard._render();
  assert(nodes(formCard.shadowRoot,'small').some(n=>n.textContent.includes('Archived legacy session')));
  formCard._tab='reports';formCard._reports=[{legacy:true,id:'invented',start:0,end:900}];formCard._render();
  assert(nodes(formCard.shadowRoot,'small').some(n=>n.textContent.includes('Archived report')));
  // Language selection, fallback, live drafts and safe interpolation.
  const localized=new Card();localized._data=data;localized._profiles={active:'example',versions:[{id:'example',profile}]};
  for(const [language,expected] of [[undefined,'Overview'],['en','Overview'],['de','Overview'],['sl','Pregled'],['sl-SI','Pregled']]) {
    localized.hass={locale:{language},callApi:async()=>{throw Error('unexpected request');}};
    localized._tab='overview';localized._render();
    assert(nodes(localized.shadowRoot,'button').some(n=>n.textContent===expected));
  }
  localized.hass={language:'sl'};assert.equal(localized._number(null),'neznano');
  assert.equal(localized._t('Missing translation'), 'Missing translation');
  assert.equal(localized._t`Version ${7}`,'Različica 7');
  for(const tab of ['overview','sessions','reports','profiles','pricing','settings','study','history']) {
    localized._tab=tab;localized.hass={language:'en'};localized._render();
    const english=nodes(localized.shadowRoot,'button').map(n=>n.textContent);
    localized.hass={language:'sl'};
    assert.notDeepEqual(nodes(localized.shadowRoot,'button').map(n=>n.textContent),english);
  }
  localized._tab='pricing';localized.hass={language:'en'};localized._render();
  let edit=nodes(localized.shadowRoot,'input')[0];edit.value='Untranslated private name';edit.events.input();
  localized._error='Invalid study settings.';
  localized.hass={language:'sl'};
  assert.equal(nodes(localized.shadowRoot,'input')[0].value,'Untranslated private name');
  assert.equal(localized._pricingDraft.name,'Untranslated private name');
  assert(nodes(localized.shadowRoot,'p').some(n=>n.textContent==='Nastavitve študije niso veljavne.'));
  localized._tab='profiles';localized._render();
  edit=nodes(localized.shadowRoot,'input')[0];edit.value='Unsaved simple profile';
  localized.hass={language:'en'};
  assert.equal(nodes(localized.shadowRoot,'input')[0].value,'Unsaved simple profile');
  localized._tab='history';localized._render();
  const selected=nodes(localized.shadowRoot,'input').find(n=>n.type==='file');selected.files=[{name:'synthetic.sqlite3'}];
  localized.hass={language:'sl'};
  assert.equal(nodes(localized.shadowRoot,'input').find(n=>n.type==='file'),selected);
  localized._importResult={converted_role_intervals:2,profiles:1,reports:1,backup:'<img src=x>'};localized._render();
  assert(nodes(localized.shadowRoot,'p').some(n=>n.textContent.includes('2 merilnih zapisov, 1 profilov, 1 poročil')));
  assert.equal(nodes(localized.shadowRoot,'img').length,0);
  localized.hass={locale:{language:'en'},language:'sl'};
  assert.equal(localized._number(null),'unknown');
  assert.equal(localized._number(1234.5,'kWh'),'1,234.5 kWh');
  // Old regional profiles show the existing basis. Changing it saves the new basis.
  const billing = new Card();
  billing._data = data;
  billing._profiles = {active:'billing',versions:[{id:'billing',profile:{...profile,regional:[{
    energy:{},power:{},agreed_kw:{},excess_mode:'informative',
  }]}}]};
  billing.hass = {language:'en',callApi:async(method,action,payload)=>{
    saved = payload;
    return billing._profiles;
  }};
  billing._tab = 'settings';
  billing._render();
  const excise = nodes(billing.shadowRoot,'label').find(n=>n.textContent==='Excise basis');
  const basis = nodes(excise,'select')[0];
  assert.equal(nodes(basis,'option').find(n=>n.selected).value,'import');
  basis.value = 'net_import';
  basis.events.change();
  billing.hass = {language:'sl',callApi:billing._hass.callApi};
  const translatedExcise = nodes(billing.shadowRoot,'label').find(n=>n.textContent==='Osnova za trošarino');
  assert.equal(nodes(translatedExcise,'option').find(n=>n.selected).value,'net_import');
  await nodes(billing.shadowRoot,'button').find(n=>n.textContent==='Shrani EV in obračun').events.click();
  assert.equal(saved.regional[0].excise_basis,'net_import');
  // Native config forms already use English source strings with matching translations.
  const base=JSON.parse(readFileSync('custom_components/energy_cost_monitor/strings.json','utf8'));
  const en=JSON.parse(readFileSync('custom_components/energy_cost_monitor/translations/en.json','utf8'));
  const sl=JSON.parse(readFileSync('custom_components/energy_cost_monitor/translations/sl.json','utf8'));
  const paths=(value,prefix='')=>Object.entries(value).flatMap(([key,item])=>typeof item==='object'?paths(item,prefix+key+'.'):[prefix+key]).sort();
  assert.deepEqual(base,en);assert.deepEqual(paths(en),paths(sl));
  console.log('Card behavior: PASS (workflows, English/Slovenian, fallback, draft/file retention, translation parity)');
})().catch(error=>{console.error(error);process.exitCode=1;});
