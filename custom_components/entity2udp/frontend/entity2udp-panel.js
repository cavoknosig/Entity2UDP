/* Entity2UDP management panel: native Home Assistant authenticated WebSocket API. */
const css = `
:host{display:block;color:var(--primary-text-color);font:14px system-ui,sans-serif}*{box-sizing:border-box}
main{max-width:1250px;margin:auto;padding:22px}header,.toolbar,.line{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.title{display:flex;align-items:center;gap:10px}.title img,.destination-icon{display:block;flex:none}
header{justify-content:space-between;margin-bottom:20px}h1{font-size:27px;margin:0}h2{font-size:19px;margin:0 0 12px}
small,.muted{color:var(--secondary-text-color)}.layout{display:grid;grid-template-columns:260px 1fr;gap:20px}
.panel{background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#ddd);border-radius:14px;padding:18px;min-width:0}
button{border:1px solid var(--divider-color,#ccc);border-radius:9px;padding:9px 13px;background:var(--secondary-background-color,#f4f5f7);color:inherit;cursor:pointer}
button.primary{background:var(--primary-color,#03a9f4);color:white;border:0}button.danger{color:var(--error-color,#c62828)}button:disabled{opacity:.5;cursor:default}
button.active{border-color:var(--primary-color);font-weight:700}.dest{display:block;width:100%;text-align:left;margin:6px 0}
input,select,textarea{background:var(--card-background-color,#fff);color:inherit;border:1px solid var(--divider-color,#bbb);border-radius:7px;padding:9px;min-width:0;width:100%;font:inherit}
label{display:block;font-size:12px;color:var(--secondary-text-color);margin:0 0 5px}.fields{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:14px}
fieldset{border:1px solid var(--divider-color);border-radius:9px;margin:12px 0;padding:12px}legend{font-weight:650}table{border-collapse:collapse;width:100%;font-size:13px}th,td{border-bottom:1px solid var(--divider-color,#ddd);padding:9px;text-align:left}td:last-child{text-align:right}th{color:var(--secondary-text-color)}
.tablewrap{overflow-x:auto}.message{padding:10px;margin:12px 0;border-radius:8px;background:var(--secondary-background-color,#eee)}.error{color:var(--error-color,#c62828)}
.modalback{position:fixed;inset:0;background:#0008;display:grid;place-items:center;z-index:1000;padding:15px}.modal{width:min(880px,100%);max-height:90vh;overflow:auto;background:var(--card-background-color,#fff);border-radius:14px;padding:22px;box-shadow:0 8px 30px #0004}
.rule-layout{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);align-items:start;gap:20px}.rule-dialog-actions{margin-top:20px}
.rule-layout .fields{grid-template-columns:repeat(2,minmax(0,1fr))}
.preview{margin:0;overflow-wrap:anywhere}.preview ul{padding-left:18px}
.mapping-row{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr) 65px 40px;gap:6px;margin:6px 0}
.toggle{display:flex;align-items:center;gap:8px}.toggle input{width:auto}
.device-brand{display:flex;align-items:center;gap:8px}
@media(max-width:650px){.rule-layout{grid-template-columns:1fr}}
.rule-filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px}
.rule-filters label{margin:0}.rule-state{display:flex;align-items:center;gap:8px;white-space:nowrap}
.rule-state input{width:32px;min-width:32px;height:18px;appearance:none;border-radius:12px;padding:0;cursor:pointer;position:relative;background:var(--divider-color,#ddd)}
.rule-state input:checked{background:var(--primary-color,#03a9f4)}
.rule-state input::before{content:'';position:absolute;top:2px;left:2px;background:white;border-radius:50%;width:12px;height:12px}
.rule-state input:checked::before{left:16px}.rule-state input:disabled{opacity:.5;cursor:default}
.group-row th{background:var(--secondary-background-color,#eee)}
.destination-nav{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.destination-nav h2{margin:0 auto 0 0;overflow-wrap:anywhere}
.rules-heading{justify-content:space-between;margin-bottom:12px}.rules-heading h2{margin:0}
.rules-table{margin-top:8px}.rules-table th{white-space:nowrap}.rules-table thead th:last-child{text-align:right}.rules-table td{overflow-wrap:anywhere}
.rules-table td:first-child{min-width:160px}.rule-actions{display:flex;gap:6px;justify-content:flex-end}
.rule-name{display:block}.pagination{justify-content:flex-end;margin-top:12px}
.pagination label{display:flex;gap:8px;align-items:center;margin:0}.pagination select{width:auto}
.destination-filters{margin-bottom:20px}
.settings-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,290px),1fr));align-items:start;gap:16px}
.settings-grid .toggle{font-size:14px;color:inherit;margin:12px 0}
.settings-grid .muted{line-height:1.5}
.activity-filters{max-width:540px;margin-bottom:12px}
.activity-table{margin-top:12px}.activity-table td:last-child{text-align:left}
.activity-table time{white-space:nowrap}.activity-table td{overflow-wrap:anywhere}
.translation-group{margin-top:14px;padding:0 12px 12px;border:1px solid var(--divider-color,#ddd);border-radius:9px}
.translation-group summary{padding:12px 0;cursor:pointer;font-weight:650}
textarea{min-height:115px;font-family:monospace}.tag{font-size:12px;padding:4px 8px;border-radius:8px;background:var(--secondary-background-color,#eee)}
@media(max-width:850px){.layout{grid-template-columns:1fr}.fields{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:500px){.fields{grid-template-columns:1fr}}
`;
const escapeHtml = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const DEFAULT_RULE = (id) => ({key:'ha_'+id.replace(/[.\-]/g,'_'),type:'auto',translations:{},scale:1,precision:3,min_delta:0,invalid_value:'-9999'});
class Entity2UDPPanel extends HTMLElement {
  constructor(){super();this.attachShadow({mode:'open'});this.destinations=[];this.selected=null;this.draft=null;this.filter='';this.view='destinations';this.page=0;this.pageSize=25;this.sidebarVisible=null;this.activity=null;this.activityDestination='';this.activityKind='';this.systemDestination=null;this.destinationFilter='';this.ruleSort='name';this.ruleGrouping=false;this.ruleStatus='all';this.initialRoute=new URLSearchParams(window.location.search);this.message='';this.modal=null;this._hass=null;this.busy=false;}
  set hass(hass){const first=!this._hass;this._hass=hass;if(first)this.load();else this.updateStatePreview();}
  async api(type,params={}){return this._hass.callWS({type:'entity2udp/'+type,...params});}
  async load() {
    try {
      this.destinations=await this.api('list');
      const route=this.initialRoute;
      const requested=this.destinations.find(item=>item.id===route?.get('destination'));
      if (route?.get('view')==='rules') {
        this.view='rules';
        this.destinationFilter=requested?.id??'';
      }
      this.initialRoute=null;
      const selected=requested||this.destinations.find(item=>item.id===this.selected)||this.destinations[0];
      if (!this.destinations.some(item=>item.id===this.destinationFilter)) this.destinationFilter='';
      this.selected=selected?.id??null;
      this.draft=selected?structuredClone(selected):null;
      this.message='';
      if (route?.get('view')==='activity') await this.openActivity();
      else if (route?.get('view')==='settings') await this.openSettings();
      else this.render();
    } catch (error) {
      this.notify('Unable to load destinations: '+error.message,true);
    }
  }
  notify(text,error=false){this.message=text;this.error=error;this.render();}
  render(){const d=this.draft;this.shadowRoot.innerHTML=`<style>${css}</style><main>
    <header><h1 class="title"><img src="/entity2udp_static/icon.png?v=2" width="48" height="48" alt="">Entity2UDP</h1><div class="toolbar"><button data-act="refresh">↻ Refresh</button>${this.view==='destinations'?'<button data-act="new">+ Add UDP destination</button>':''}</div></header>
    ${this.message?`<div class="message ${this.error?'error':''}" role="status">${escapeHtml(this.message)}</div>`:''}
    ${this.destinationNav()}
    ${this.view==='rules'?this.rulesHtml():this.view==='settings'?this.settingsHtml():this.view==='activity'?this.activityHtml():`<div class="layout">${this.destinationList()}
    <section>${d?`<div class="panel"><div class="line" style="justify-content:space-between"><h2>Destination settings</h2><div class="line"><span class="tag">${d.sent} sent · ${d.errors} errors</span><div class="device-brand"><img class="destination-icon" src="/entity2udp_static/icon.png?v=2" width="64" height="64" alt=""><span>Entity2UDP Device</span></div></div></div>
    <div class="fields"><div><label>Name</label><input data-setting="name" value="${escapeHtml(d.name)}"></div><div><label>Host / IP</label><input data-setting="host" value="${escapeHtml(d.host)}"></div><div><label>UDP port</label><input data-setting="port" type="number" min="1" max="65535" value="${d.port}"></div>
    <div><label title="Value sent when an entity is unavailable or its state cannot be converted.">Fallback value</label><input data-setting="invalid_value" value="${escapeHtml(d.invalid_value)}"></div><div><label>Startup sync</label><select data-setting="startup_resync"><option value="true" ${d.startup_resync?'selected':''}>Enabled</option><option value="false" ${!d.startup_resync?'selected':''}>Disabled</option></select></div></div>
    <details class="destination-filters" ${d.min_interval_seconds||d.periodic_resend_seconds?'open':''}><summary>Filtering and resends</summary>
    <fieldset><legend>Destination defaults</legend>
    <label class="toggle"><input type="checkbox" data-toggle="min_interval_seconds" ${d.min_interval_seconds?'checked':''}>Limit how often values are sent</label>
    <label>Minimum interval (seconds)<input data-setting="min_interval_seconds" type="number" min="0.01" max="86400" step="any" value="${d.min_interval_seconds||1}" ${d.min_interval_seconds?'':'disabled'}></label>
    <label class="toggle"><input type="checkbox" data-toggle="periodic_resend_seconds" ${d.periodic_resend_seconds?'checked':''}>Periodically resend all values</label>
    <label>Resend interval (seconds)<input data-setting="periodic_resend_seconds" type="number" min="5" max="86400" step="1" value="${d.periodic_resend_seconds||20}" ${d.periodic_resend_seconds?'':'disabled'}></label>
    </fieldset></details>
    <div class="toolbar"><button class="primary" data-act="save">Save changes</button><button data-act="sync">Send all now</button><button data-act="destination-rules">Manage configured entities</button><button class="danger" data-act="delete">Remove destination</button></div></div>`:'<div class="panel">Select or add a destination to begin.</div>'}</section></div>`}
    </main>${this.modal?this.modalHtml():''}`;
    this.shadowRoot.querySelectorAll('[data-select]').forEach(el=>el.addEventListener('click',()=>this.selectDestination(el.dataset.select)));
    this.shadowRoot.querySelectorAll('[data-setting]').forEach(el=>el.addEventListener('change',()=>{let v=el.value;if(el.dataset.setting==='startup_resync')v=v==='true';if(['port','min_interval_seconds','periodic_resend_seconds'].includes(el.dataset.setting))v=Number(v);this.draft[el.dataset.setting]=v;}));
    this.shadowRoot.querySelectorAll('[data-toggle]').forEach(el=>el.addEventListener('change',()=>{
      const key=el.dataset.toggle;
      const input=this.shadowRoot.querySelector(`[data-setting="${key}"]`);
      input.disabled=!el.checked;
      this.draft[key]=el.checked?Number(input.value):0;
    }));
    this.shadowRoot.querySelector('[data-filter]')?.addEventListener('input',e=>{
      const {value,selectionStart,selectionEnd}=e.target;
      this.filter=value;
      this.page=0;
      this.render();
      const filter=this.shadowRoot.querySelector('[data-filter]');
      filter.focus();
      filter.setSelectionRange(selectionStart,selectionEnd);
    });
    this.shadowRoot.querySelectorAll('[data-rule-filter]').forEach(el=>el.addEventListener('change',()=>{
      this[el.dataset.ruleFilter]=el.type==='checkbox'?el.checked:el.dataset.ruleFilter==='pageSize'?Number(el.value):el.value;
      this.page=0;
      this.render();
    }));
    this.shadowRoot.querySelectorAll('[data-edit]').forEach(el=>el.addEventListener('click',()=>{
      if (this.selectDestination(el.dataset.entry)) this.openRule(el.dataset.edit);
    }));
    this.shadowRoot.querySelectorAll('[data-remove]').forEach(el=>el.addEventListener('click',()=>{
      if (!this.selectDestination(el.dataset.entry)) return;
      if (confirm('Remove export rule for '+el.dataset.remove+'?')) {
        delete this.draft.entities[el.dataset.remove];
        this.render();
      }
    }));
    this.shadowRoot.querySelectorAll('[data-activity-filter]').forEach(el=>el.addEventListener('change',()=>{
      this[el.dataset.activityFilter]=el.value;
      this.render();
    }));
    this.shadowRoot.querySelector('[data-sidebar-visible]')?.addEventListener('change',event=>this.saveSidebar(event.target));
    this.shadowRoot.querySelector('[data-system-destination]')?.addEventListener('change',event=>{
      this.systemDestination=event.target.value;
      this.render();
    });
    this.shadowRoot.querySelectorAll('[data-enabled]').forEach(el=>el.addEventListener('change',()=>this.setRuleEnabled(el)));
    this.shadowRoot.querySelectorAll('[data-act]').forEach(el=>el.addEventListener('click',()=>this.action(el.dataset.act)));
    this.bindModal();
    this.bindRuleEditor();
  }
  destinationList() {
    return `<aside class="panel"><h2>Destinations</h2>${this.destinations.map(x=>`<button class="dest ${x.id===this.selected?'active':''}" data-select="${escapeHtml(x.id)}">${escapeHtml(x.name)}<br><small>${escapeHtml(x.host)}:${x.port} · ${Object.keys(x.entities).length} entities</small></button>`).join('')||'<p class="muted">No destinations yet.</p>'}</aside>`;
  }
  destinationNav() {
    const destinations=this.view==='destinations';
    return `<nav class="destination-nav" aria-label="Entity2UDP views">
      <button class="${destinations?'active':''}" aria-pressed="${destinations}" data-act="destinations">Destinations</button>
      <button class="${this.view==='rules'?'active':''}" aria-pressed="${this.view==='rules'}" data-act="rules">Configured entities</button>
      <button class="${this.view==='settings'?'active':''}" aria-pressed="${this.view==='settings'}" data-act="settings">Settings</button>
      <button class="${this.view==='activity'?'active':''}" aria-pressed="${this.view==='activity'}" data-act="activity">Activity</button>
    </nav>`;
  }
  rulesHtml() {
    const query=this.filter.trim().toLowerCase();
    const pageSize=this.pageSize;
    const status=this.ruleStatus;
    const filter=this.destinationFilter;
    const rows=this.destinations.filter(item=>!filter||item.id===filter).flatMap(saved=>{
      const destination=saved.id===this.selected?this.draft:saved;
      return Object.entries(destination.entities).map(([id,rule])=>({
        id,rule,destination,saved:Object.hasOwn(saved.entities,id),
        name:this._hass.states?.[id]?.attributes?.friendly_name||id
      }));
    }).filter(row=>{
      const enabled=row.rule.enabled!==false;
      return (status==='all'||(status==='enabled'?enabled:!enabled))
        && [row.id,row.name,row.rule.key].some(value=>String(value??'').toLowerCase().includes(query));
    });
    const byDestination=(a,b)=>a.destination.name.localeCompare(b.destination.name);
    const byName=(a,b)=>a.name.localeCompare(b.name,undefined,{numeric:true});
    rows.sort((a,b)=>{
      if(this.ruleGrouping) {
        const groupOrder=byDestination(a,b)||a.destination.id.localeCompare(b.destination.id);
        if(groupOrder) return groupOrder;
      }
      const order=this.ruleSort==='destination'?byDestination(a,b):byName(a,b)*(this.ruleSort==='name-desc'?-1:1);
      return order||byName(a,b)||a.id.localeCompare(b.id);
    });
    const lastPage=Math.max(0,Math.ceil(rows.length/pageSize)-1);
    this.page=Math.min(this.page,lastPage);
    const first=this.page*pageSize;
    const visible=rows.slice(first,first+pageSize);
    const target=filter||this.selected;
    const destinationOptions=this.destinations.map(item=>`<option value="${escapeHtml(item.id)}" ${item.id===filter?'selected':''}>${escapeHtml(item.name)}</option>`).join('');
    return `<section class="panel" aria-label="Configured entities">
      <div class="line rules-heading"><h2>Configured entities</h2><div class="toolbar">
        <button class="primary" data-act="add" ${target?'':'disabled'}>+ Add entity rule</button>
        <button data-act="export" ${target?'':'disabled'}>Download rules JSON</button>
        <button data-act="import" ${target?'':'disabled'}>Import rules JSON</button>
        <button data-act="save" ${this.draft?'':'disabled'}>Save changes</button>
      </div></div>
      ${target?`<p class="muted">Add, import and download for <strong>${escapeHtml((this.destinations.find(item=>item.id===target)||{}).name)}</strong>.</p>`:''}
      <div class="rule-filters">
        <label>Search<input type="search" data-filter placeholder="Name, entity ID or UDP key" value="${escapeHtml(this.filter)}"></label>
        <label>Destination<select data-rule-filter="destinationFilter"><option value="">All destinations</option>${destinationOptions}</select></label>
        <label>Status<select data-rule-filter="ruleStatus">${[['all','All rules'],['enabled','Enabled'],['paused','Paused']].map(([key,label])=>`<option value="${key}" ${status===key?'selected':''}>${label}</option>`).join('')}</select></label>
        <label>Sort by<select data-rule-filter="ruleSort">${[['name','Name (A–Z)'],['name-desc','Name (Z–A)'],['destination','Destination']].map(([key,label])=>`<option value="${key}" ${this.ruleSort===key?'selected':''}>${label}</option>`).join('')}</select></label>
        <label class="toggle"><input type="checkbox" data-rule-filter="ruleGrouping" ${this.ruleGrouping?'checked':''}>Group by destination</label>
      </div>
      <div class="tablewrap rules-table"><table><thead><tr><th scope="col">Home Assistant entity</th><th scope="col">Destination</th><th scope="col">UDP key</th><th scope="col">Forwarding</th><th scope="col">Actions</th></tr></thead><tbody>
        ${visible.map(({id,name,rule,destination,saved},index)=>{
          const entry=escapeHtml(destination.id);
          const escapedId=escapeHtml(id);
          const enabled=rule.enabled!==false;
          const group=this.ruleGrouping&&visible[index-1]?.destination.id!==destination.id
            ?`<tr class="group-row"><th colspan="5">${escapeHtml(destination.name)}</th></tr>`:'';
          return `${group}<tr>
            <td>${name===id?'':`<strong class="rule-name">${escapeHtml(name)}</strong>`}<small>${escapedId}</small></td>
            <td>${escapeHtml(destination.name)}</td><td><code>${escapeHtml(rule.key)}</code></td>
            <td><label class="rule-state"><input type="checkbox" role="switch" data-enabled="${escapedId}" data-entry="${entry}" aria-label="Forward ${escapedId} to ${escapeHtml(destination.name)}" ${enabled?'checked':''} ${saved?'':'disabled'}>${saved?(enabled?'Enabled':'Paused'):'Unsaved'}</label></td>
            <td><div class="rule-actions"><button data-edit="${escapedId}" data-entry="${entry}">Edit</button><button class="danger" data-remove="${escapedId}" data-entry="${entry}">Remove</button></div></td>
          </tr>`;
        }).join('')||`<tr><td colspan="5">No matching export rules</td></tr>`}
      </tbody></table></div>
      <div class="line pagination"><label>Rows per page
        <select data-rule-filter="pageSize">${[25,50,100].map(size=>`<option value="${size}" ${size===pageSize?'selected':''}>${size}</option>`).join('')}</select>
      </label><span role="status">${rows.length?`${first+1}–${first+visible.length} of ${rows.length}`:'0 rules'}</span>
        <button data-act="previous" ${this.page?'':'disabled'}>Previous</button>
        <button data-act="next" ${this.page<lastPage?'':'disabled'}>Next</button>
      </div>
    </section>`;
  }
  activityHtml() {
    const data=this.activity;
    const destinations=new Map(this.destinations.map(item=>[item.id,item.name]));
    for(const item of data?.events??[]) {
      if(!destinations.has(item.destination_id))destinations.set(item.destination_id,item.destination);
    }
    const events=(data?.events??[]).filter(item=>
      (!this.activityDestination||this.activityDestination===item.destination_id)
      && (!this.activityKind||this.activityKind===item.kind));
    return `<section class="panel" aria-label="Activity">
      <h2>Activity</h2>
      <p class="muted">Resends and errors from this Home Assistant session. Activity clears on restart${data?` and keeps the latest ${escapeHtml(data.limit)} events`:''}.</p>
      <div class="rule-filters activity-filters">
        <label>Destination<select data-activity-filter="activityDestination">
          <option value="">All destinations</option>
          ${[...destinations].map(([id,name])=>`<option value="${escapeHtml(id)}" ${id===this.activityDestination?'selected':''}>${escapeHtml(name)}</option>`).join('')}
        </select></label>
        <label>Type<select data-activity-filter="activityKind">
          ${[['','All activity'],['resend','Resends'],['error','Errors']].map(([value,label])=>`<option value="${value}" ${value===this.activityKind?'selected':''}>${label}</option>`).join('')}
        </select></label>
      </div>
      ${events.length?`<div class="tablewrap activity-table"><table>
        <thead><tr><th scope="col">Time</th><th scope="col">Destination</th><th scope="col">Event</th></tr></thead>
        <tbody>${events.map(item=>`<tr>
          <td><time datetime="${escapeHtml(item.timestamp)}">${escapeHtml(new Date(item.timestamp).toLocaleString())}</time></td>
          <td>${escapeHtml(item.destination)}</td>
          <td class="${item.kind==='error'?'error':''}">${escapeHtml(item.message)}</td>
        </tr>`).join('')}</tbody>
      </table></div>`:`<p role="status">${data?'No matching activity.':'Loading activity…'}</p>`}
    </section>`;
  }
  async openActivity() {
    this.view='activity';
    this.render();
    try {
      this.activity=await this.api('activity');
      if(this.view==='activity')this.render();
    } catch(error) {
      if(this.view==='activity')this.notify('Could not load activity: '+error.message,true);
    }
  }
  settingsHtml() {
    const destination=this.systemSettingsDestination();
    return `<section class="settings-grid" aria-label="Settings">
      <div class="panel">
        <h2>Sidebar shortcut</h2>
        <label class="toggle">
          <input type="checkbox" data-sidebar-visible ${this.sidebarVisible===true?'checked':''} ${this.sidebarVisible===null||this.busy?'disabled':''}>
          Show Entity2UDP in the sidebar
        </label>
        <p class="muted">The management panel stays available from Devices & Services when the shortcut is hidden.</p>
      </div>
      <div class="panel">
        <h2>Home Assistant system options</h2>
        ${destination?`<label>Destination
          <select data-system-destination>${this.destinations.map(item=>`<option value="${escapeHtml(item.id)}" ${item.id===destination.id?'selected':''}>${escapeHtml(item.name)}</option>`).join('')}</select>
        </label>
        <label class="toggle"><input type="checkbox" data-enable-new-entities ${destination.pref_disable_new_entities?'':'checked'}>Enable newly added Home Assistant entities</label>
        <button data-act="save-system" ${this.busy?'disabled':''}>Save system options</button>`:'<p>Add a destination to configure its system options.</p>'}
      </div>
    </section>`;
  }
  systemSettingsDestination() {
    return this.destinations.find(item=>item.id===(this.systemDestination||this.selected))||this.destinations[0];
  }
  async openSettings() {
    this.view='settings';
    this.render();
    try {
      const settings=await this.api('panel_settings');
      this.sidebarVisible=settings.show_in_sidebar;
      if(this.view==='settings')this.render();
    } catch (error) {
      if(this.view==='settings')this.notify('Could not load sidebar settings: '+error.message,true);
    }
  }
  async saveSidebar(input) {
    if(this.busy)return;
    this.busy=true;
    input.disabled=true;
    try {
      const settings=await this.api('panel_settings',{show_in_sidebar:input.checked});
      this.sidebarVisible=settings.show_in_sidebar;
      this.message=settings.show_in_sidebar?'Sidebar shortcut shown.':'Sidebar shortcut hidden.';
      this.error=false;
    } catch (error) {
      this.message=error.message;
      this.error=true;
    } finally {
      this.busy=false;
      this.render();
    }
  }
  async saveSystemSettings() {
    const destination=this.systemSettingsDestination();
    if(!destination)return;
    const fields={
      pref_disable_new_entities:!this.shadowRoot.querySelector('[data-enable-new-entities]').checked,
    };
    this.busy=true;
    try {
      const result=await this._hass.callWS({type:'config_entries/update',entry_id:destination.id,...fields});
      Object.assign(destination,fields);
      if(this.draft?.id===destination.id)Object.assign(this.draft,fields);
      this.message=result.require_restart?'System options saved. Restart Home Assistant to apply them.':'System options saved.';
      this.error=false;
    } catch (error) {
      this.message=error.message;
      this.error=true;
    } finally {
      this.busy=false;
      this.render();
    }
  }
  async setRuleEnabled(input) {
    const entryId=input.dataset.entry;
    const entityId=input.dataset.enabled;
    const enabled=input.checked;
    if (this.busy) {this.render();return;}
    this.busy=true;
    input.disabled=true;
    try {
      await this.api('set_rule_enabled',{entry_id:entryId,entity_id:entityId,enabled});
      const saved=this.destinations.find(item=>item.id===entryId);
      if (saved?.entities[entityId]) saved.entities[entityId].enabled=enabled;
      if (this.selected===entryId&&this.draft?.entities[entityId]) this.draft.entities[entityId].enabled=enabled;
      this.notify(enabled?'Forwarding enabled.':'Forwarding paused.');
    } catch (error) {
      this.notify(error.message,true);
    } finally {
      this.busy=false;
    }
  }
  canDiscard() {
    const saved=this.destinations.find(d=>d.id===this.selected);
    return JSON.stringify(saved)===JSON.stringify(this.draft)||!this.draft
      ||confirm('Discard unsaved destination changes?');
  }
  selectDestination(id) {
    if (id===this.selected) return true;
    if (!this.canDiscard()) return false;
    this.selected=id;
    this.draft=structuredClone(this.destinations.find(d=>d.id===id));
    this.render();
    return true;
  }
  async action(act){if(this.busy)return;try{if(act==='activity'){await this.openActivity();return;}if(act==='settings'){await this.openSettings();return;}if(act==='save-system'){await this.saveSystemSettings();return;}if(act==='destination-rules'){this.destinationFilter=this.selected;this.page=0;this.view='rules';this.render();return;}if(act==='destinations'||act==='rules'){this.view=act;this.render();return;}if(act==='previous'||act==='next'){this.page+=act==='next'?1:-1;this.render();return;}if(act==='refresh'&&this.view==='activity'){await this.openActivity();return;}if(act==='refresh'){if(this.canDiscard()){await this.load();if(this.view==='settings')await this.openSettings();}return;}if(act==='new'){this.modal={kind:'destination'};this.render();return;}if(act==='delete'){if(confirm('Permanently delete destination '+this.draft.name+' and all its export rules?')){await this.api('delete',{entry_id:this.selected});await this.load();this.notify('Destination removed.');}return;}if(act==='save'){if([...this.shadowRoot.querySelectorAll('[data-setting]')].some(input=>!input.reportValidity()))return;const d=this.draft;await this.api('save',{entry_id:d.id,settings:{name:d.name,host:d.host,port:d.port,invalid_value:d.invalid_value,min_interval_seconds:d.min_interval_seconds,periodic_resend_seconds:d.periodic_resend_seconds??0,startup_resync:d.startup_resync},entities:d.entities});await this.load();this.notify('Saved. Destination reload may take a moment.');return;}if(act==='sync'){const result=await this.api('sync',{entry_id:this.selected});this.notify(`Sent ${result.resend_sent} values${result.resend_failed?` · ${result.resend_failed} failed`:''}.`,Boolean(result.resend_failed));return;}if(['add','export','import'].includes(act)){const target=this.destinationFilter||this.selected;if(!target||!this.selectDestination(target))return;}if(act==='add'){this.openRule();return;}if(act==='export'){this.exportJson();return;}if(act==='import'){if(!this.canDiscard())return;this.modal={kind:'import'};this.render();return;}}catch(e){this.notify(e.message,true);}}
  openRule(id=null){this.modal={kind:'rule',id,entity_id:id||'',rule:structuredClone(id?this.draft.entities[id]:DEFAULT_RULE('sensor.example'))};this.render();}
  modalHtml(){const m=this.modal;if(m.kind==='destination')return `<div class="modalback"><div class="modal"><h2>Add UDP destination</h2><div class="fields"><div><label>Name</label><input id="newname" value="New destination"></div><div><label>Host / IP</label><input id="newhost" placeholder="192.168.1.50"></div><div><label>UDP port</label><input id="newport" type="number" value="7000"></div></div><div class="toolbar"><button class="primary" data-modal="createdest">Create</button><button data-modal="cancel">Cancel</button></div></div></div>`;if(m.kind==='import')return `<div class="modalback"><div class="modal"><h2>Import entity rules</h2><p class="muted">Import a full or partial Entity2UDP JSON export into this destination.</p><label>Mode</label><select id="importmode"><option value="merge">Merge with existing</option><option value="replace">Replace all rules</option></select><label style="margin-top:12px">JSON configuration</label><textarea id="importjson" placeholder='{"schema_version":1,"entities":{...}}'></textarea><div class="toolbar"><button class="primary" data-modal="doimport">Import</button><button data-modal="cancel">Cancel</button></div></div></div>`;
    return this.ruleHtml(m);
  }
  ruleHtml(m) {
    const r=m.rule;
    const intervalMode=r.min_interval_seconds==null?'inherit':r.min_interval_seconds>0?'custom':'off';
    return `<div class="modalback"><div class="modal" role="dialog" aria-modal="true" aria-label="Export rule">
      <div class="rule-layout"><div>
        <h2>${m.id?'Edit':'Add'} export rule</h2>
        <div class="fields">
          <label>Home Assistant entity<input id="entityid" placeholder="Search entity ID" list="haentities" value="${escapeHtml(m.entity_id)}" ${m.id?'disabled':''}></label>
          <datalist id="haentities">${Object.entries(this._hass.states||{}).filter(([id])=>!this.draft.entities[id]).map(([id,state])=>`<option value="${escapeHtml(id)}" label="${escapeHtml(state.attributes?.friendly_name||id)}"></option>`).join('')}</datalist>
          <label>UDP key<input id="key" value="${escapeHtml(r.key)}" required pattern="[A-Za-z][A-Za-z0-9_]*"></label>
          <label>Type<select id="type">${['auto','number','boolean','text'].map(x=>`<option value="${x}" ${r.type===x?'selected':''}>${x}</option>`).join('')}</select></label>
          <label>Scale<input id="scale" type="number" step="any" value="${r.scale}" required></label>
          <label>Decimal places<input id="precision" type="number" min="0" max="10" value="${r.precision}" required></label>
          <label>Fallback value<input id="invalid_value" pattern="-?[0-9]+([.][0-9]+)?" value="${escapeHtml(r.invalid_value)}" required></label>
        </div>
        <fieldset><legend>Filtering</legend>
          <label>Update interval<select id="interval-mode">${[['inherit','Use destination default'],['off','Send without an interval limit'],['custom','Set a minimum interval']].map(([key,label])=>`<option value="${key}" ${key===intervalMode?'selected':''}>${label}</option>`).join('')}</select></label>
          <label>Minimum interval (seconds)<input id="min_interval_seconds" type="number" min="0.01" max="86400" step="any" value="${r.min_interval_seconds||1}" ${intervalMode==='custom'?'':'disabled'} required></label>
          <label class="toggle"><input type="checkbox" id="delta-enabled" ${r.min_delta?'checked':''}>Only send significant numeric changes</label>
          <label>Minimum numeric change<input id="min_delta" type="number" min="0" step="any" value="${r.min_delta||1}" ${r.min_delta?'':'disabled'} required></label>
        </fieldset>
        <details class="translation-group" ${Object.keys(r.translations||{}).length?'open':''}><summary>State translations</summary>
          <p id="cover-defaults" class="muted" hidden>Cover defaults in Auto mode: closed = 0, open = 1, opening = 2, closing = 3. Your mappings override these values.</p>
          <div id="mapping-rows">${Object.entries(r.translations||{}).map(([source,value])=>this.mappingRow(source,value)).join('')}</div>
          <div class="toolbar"><button data-modal="addmapping">Add mapping</button><button data-modal="mapstate" id="map-state">Map current state</button></div>
        </details>
      </div><aside class="panel preview"><h2>Entity state</h2>
        <p id="current-state" aria-live="polite"></p><h3>Last hour</h3><div id="state-history"></div>
      </aside></div>
      <div class="toolbar rule-dialog-actions"><button class="primary" data-modal="saverule">Apply rule</button><button data-modal="cancel">Cancel</button></div>
    </div></div>`;
  }
  mappingRow(source='',value='') {
    const type=typeof value;
    return `<div class="mapping-row">
      <input aria-label="Home Assistant state" placeholder="HA state" value="${escapeHtml(source)}">
      <input aria-label="UDP value" placeholder="UDP value" value="${escapeHtml(value)}">
      <select aria-label="Mapping value type">${['string','number','boolean'].map(t=>`<option value="${t}" ${type===t?'selected':''}>${{string:'Text',number:'Num',boolean:'Bool'}[t]}</option>`).join('')}</select>
      <button type="button" aria-label="Remove mapping" data-drop-mapping>×</button>
    </div>`;
  }
  bindRuleEditor() {
    const get=id=>this.shadowRoot.getElementById(id);
    const entity=get('entityid');
    if (!entity) return;
    entity.addEventListener('input',()=>{
      const key=get('key');
      if (!key.dataset.edited) key.value=entity.value?DEFAULT_RULE(entity.value).key:'';
      this.updateStatePreview();
    });
    get('key').addEventListener('input',()=>{get('key').dataset.edited='true';});
    get('interval-mode').addEventListener('change',e=>{get('min_interval_seconds').disabled=e.target.value!=='custom';});
    get('delta-enabled').addEventListener('change',e=>{get('min_delta').disabled=!e.target.checked;});
    get('mapping-rows').addEventListener('click',e=>{if(e.target.matches('[data-drop-mapping]'))e.target.closest('.mapping-row').remove();});
    this.updateStatePreview();
  }
  updateStatePreview() {
    const get=id=>this.shadowRoot.getElementById(id);
    const entityId=get('entityid')?.value.trim();
    const current=get('current-state');
    if (!current) return;
    const state=this._hass.states?.[entityId];
    current.textContent=state?.state??'Select an available entity.';
    get('map-state').disabled=!state;
    get('cover-defaults').hidden=!entityId?.startsWith('cover.');
    const history=get('state-history');
    if (history.dataset.entity===entityId) return;
    history.dataset.entity=entityId;
    if (!state) {history.textContent='';delete history.dataset.entity;return;}
    history.textContent='Loading history…';
    this._hass.callWS({type:'history/history_during_period',
      start_time:new Date(Date.now()-3600000).toISOString(),entity_ids:[entityId],
      minimal_response:true,no_attributes:true
    }).then(result=>{
      if (!history.isConnected||history.dataset.entity!==entityId) return;
      const rows=(result[entityId]||[]).slice(-8).reverse();
      history.innerHTML=rows.length?`<ul>${rows.map(row=>{
        const time=new Date((row.lc??row.lu)*1000).toLocaleTimeString();
        return `<li><time>${escapeHtml(time)}</time> · ${escapeHtml(row.s)}</li>`;
      }).join('')}</ul>`:'No recorded states in the last hour.';
    }).catch(()=>{if(history.isConnected&&history.dataset.entity===entityId)history.textContent='History unavailable.';});
  }
  readRule() {
    const get=id=>this.shadowRoot.getElementById(id);
    const id=get('entityid').value.trim();
    if (!id || (!this.modal.id&&!this._hass.states?.[id])) throw Error('Select a Home Assistant entity');
    if (!this.modal.id&&this.draft.entities[id]) throw Error('Entity already configured');
    const inputs=[...this.shadowRoot.querySelectorAll('.modal input')];
    if (inputs.some(input=>!input.reportValidity())) throw Error('Check the highlighted rule fields');
    const mappings=new Map();
    for (const row of get('mapping-rows').children) {
      const [source, target, type]=[...row.querySelectorAll('input,select')].map(input=>input.value);
      if (!source||mappings.has(source)) throw Error('Enter a unique Home Assistant state for each mapping');
      let value=target;
      if (type==='number') {
        value=Number(target);
        if (!target.trim()||!Number.isFinite(value)) throw Error('Enter a valid numeric mapping');
      }
      if (type==='boolean') {
        if (!['true','false'].includes(target)) throw Error('Boolean mappings accept true or false');
        value=target==='true';
      }
      mappings.set(source,value);
    }
    const rule={key:get('key').value.trim(),type:get('type').value,
      scale:Number(get('scale').value),precision:Number(get('precision').value),
      min_delta:get('delta-enabled').checked?Number(get('min_delta').value):0,
      invalid_value:get('invalid_value').value,translations:Object.fromEntries(mappings)};
    const mode=get('interval-mode').value;
    if (mode!=='inherit') rule.min_interval_seconds=mode==='custom'?Number(get('min_interval_seconds').value):0;
    if (typeof this.draft.entities[id]?.enabled==='boolean') rule.enabled=this.draft.entities[id].enabled;
    this.draft.entities[id]=rule;
  }
  bindModal(){this.shadowRoot.querySelectorAll('[data-modal]').forEach(el=>el.addEventListener('click',async()=>{const action=el.dataset.modal;if(action==='cancel'){this.modal=null;this.render();return;}try{if(action==='createdest'){const get=id=>this.shadowRoot.getElementById(id).value;await this.api('create',{settings:{name:get('newname'),host:get('newhost'),port:Number(get('newport')),invalid_value:'-9999',min_interval_seconds:0,startup_resync:true}});this.modal=null;await this.load();this.notify('Destination created.');return;}if(action==='addmapping'||action==='mapstate'){
      const id=this.shadowRoot.getElementById('entityid').value.trim();
      const source=action==='mapstate'?this._hass.states?.[id]?.state:'';
      const rows=this.shadowRoot.getElementById('mapping-rows');
      rows.insertAdjacentHTML('beforeend',this.mappingRow(source));
      rows.lastElementChild.querySelector('input').focus();
      return;
    }
    if(action==='saverule'){this.readRule();this.modal=null;this.render();return;}if(action==='doimport'){const doc=JSON.parse(this.shadowRoot.getElementById('importjson').value);const mode=this.shadowRoot.getElementById('importmode').value;await this.api('import',{entry_id:this.selected,document:doc,mode});this.modal=null;await this.load();this.notify('Configuration imported.');}}catch(e){alert('Invalid configuration: '+e.message);}}));}
  exportJson(){const d=this.draft;const doc={schema_version:1,project:'Entity2UDP',destinations:[{name:d.name,host:d.host,port:d.port,entities:d.entities}]};const blob=new Blob([JSON.stringify(doc,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='entity2udp-'+d.name.toLowerCase().replace(/[^a-z0-9]+/g,'-')+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
}
customElements.define('entity2udp-panel',Entity2UDPPanel);
