// Behavioral card tests with a minimal DOM double; not a browser/HA frontend test.
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
class Element {
  constructor(tag) { this.tag=tag; this.children=[]; this.events={}; this.attrs={}; this.style={}; }
  append(child) { this.children.push(child); }
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
  await card._refresh();assert.equal(calls,3);assert.equal(card._data,data);
  card._tab='profiles';card._render();
  let editor=nodes(card.shadowRoot,'textarea')[0];editor.value='unfinished profile';editor.events.input();
  await card._refresh();assert.equal(calls,3,'refresh must not discard edits');
  card._render();assert.equal(nodes(card.shadowRoot,'textarea')[0].value,'unfinished profile');
  const discard=nodes(card.shadowRoot,'button').find(n=>n.textContent==='Zavrzi osnutek');discard.events.click();assert.equal(card._draft,null);
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
  nodes(formCard.shadowRoot,'button').find(n=>n.textContent==='Pripravi profil').events.click();
  const profile=JSON.parse(formCard._draft);assert.equal(profile.scenarios[0].versions[0].export[0].value,null);
  assert.equal(profile.scenarios[0].versions[0].subscription.value,'0');
  formCard._tab='sessions';formCard._data={...data,sessions:[{legacy:true,start:0,end:900,body:{kwh:1,charging_seconds:60,pause_seconds:10,partial:true}}]};formCard._render();
  assert(nodes(formCard.shadowRoot,'small').some(n=>n.textContent.includes('Arhivirana seja')));
  formCard._tab='reports';formCard._reports=[{legacy:true,id:'invented',start:0,end:900}];formCard._render();
  assert(nodes(formCard.shadowRoot,'small').some(n=>n.textContent.includes('Arhivirano poročilo')));
  console.log('Card behavior: PASS (refresh, draft retention, discard, literal text, disconnect, profile form, legacy labels)');
})().catch(error=>{console.error(error);process.exitCode=1;});
