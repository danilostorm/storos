"use strict";
/* StorOS mockup-faithful dashboard. Numbers are taken only from current local observations. */
const $ = id => document.getElementById(id);
const ICONS = {
  house:'<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>',
  search:'<circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 5 5"/>',
  'hard-drive':'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 12h18"/><circle cx="7" cy="16" r="1"/>',
  users:'<circle cx="9" cy="8" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2M17 5a3 3 0 0 1 0 6m1 3a5 5 0 0 1 3 5"/>',
  folder:'<path d="M3 6h7l2 2h9v11H3z"/>',
  box:'<path d="m12 2 9 5-9 5-9-5zM3 7v10l9 5 9-5V7M12 12v10"/>',
  container:'<rect x="4" y="6" width="16" height="12" rx="2"/><path d="M8 3v3m8-3v3M8 18v3m8-3v3M1 10h3m-3 4h3m16-4h3m-3 4h3"/>',
  layers:'<path d="m12 2 9 5-9 5-9-5zm-9 10 9 5 9-5M3 17l9 5 9-5"/>',
  image:'<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8" cy="8" r="1.2"/><path d="m21 16-6-6-9 9"/>',
  network:'<circle cx="12" cy="4" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><path d="M12 6v6M5 17v-5h14v5"/>',
  database:'<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v13c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>',
  file:'<path d="M6 2h8l5 5v15H6zM14 2v5h5"/>',
  grid:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  package:'<path d="m12 2 9 5v10l-9 5-9-5V7zM3 7l9 5 9-5M12 12v10"/>',
  refresh:'<path d="M20 7a8 8 0 0 0-14-2L3 8m0-5v5h5M4 17a8 8 0 0 0 14 2l3-3m0 5v-5h-5"/>',
  monitor:'<rect x="3" y="3" width="18" height="14" rx="2"/><path d="M12 17v4M7 21h10"/>',
  settings:'<circle cx="12" cy="12" r="3"/><path d="M10 2h4l1 3 3 1 3-1 2 4-2 2v3l2 2-2 4-3-1-3 1-1 3h-4l-1-3-3-1-3 1-2-4 2-2v-3L1 9l2-4 3 1 3-1z"/>',
  bell:'<path d="M18 8a6 6 0 0 0-12 0c0 7-3 8-3 9h18c0-1-3-2-3-9M10 21h4"/>',
  clipboard:'<rect x="5" y="4" width="14" height="18" rx="2"/><rect x="9" y="2" width="6" height="4" rx="1"/><path d="M9 11h6m-6 4h6"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/>',
  activity:'<path d="M2 12h5l3-8 4 16 3-8h5"/>',
  copy:'<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
  moon:'<path d="M20 16a9 9 0 0 1-12-12A9 9 0 1 0 20 16z"/>',
  terminal:'<path d="m4 6 6 6-6 6m9 0h7"/>',
  user:'<circle cx="12" cy="8" r="4"/><path d="M4 22a8 8 0 0 1 16 0"/>',
  cpu:'<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 1v5m6-5v5M9 18v5m6-5v5M1 9h5m-5 6h5m12-6h5m-5 6h5"/>',
  memory:'<rect x="3" y="7" width="18" height="10" rx="2"/><path d="M7 10v4m4-4v4m4-4v4m4-4v4M6 4v3m5-3v3m5-3v3M6 17v3m5-3v3m5-3v3"/>',
  wallet:'<rect x="3" y="6" width="18" height="15" rx="2"/><path d="M3 10h18M6 6V4h13m-4 12h3"/>'
};
const NODE_SVG = 'http://www.w3.org/2000/svg';
function applyIcons(container=document) {
  container.querySelectorAll('[data-icon]').forEach(i => {
    const name = i.getAttribute('data-icon');
    const svg=document.createElementNS(NODE_SVG,'svg');
    svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');
    svg.setAttribute('stroke-linecap','round');svg.setAttribute('stroke-linejoin','round');
    svg.innerHTML=ICONS[name]||ICONS.grid;
    i.replaceWith(svg);
  });
}
const VIEW_NAMES={overview:'Visão geral',storage:'Armazenamento',shares:'Compartilhamentos',users:'Usuários',containers:'Containers',compose:'Docker Compose',images:'Imagens Docker','docker-network':'Redes Docker',volumes:'Volumes Docker',logs:'Logs Docker',catalog:'Loja de aplicativos',installed:'Aplicativos instalados',updates:'Atualizações',vms:'Máquinas virtuais',isos:'ISOs','vm-networks':'Redes de VMs',templates:'Modelos',network:'Rede',system:'Sistema',settings:'Configurações',notifications:'Notificações',tasks:'Tarefas em segundo plano',backup:'Backup',monitoring:'Monitoramento',billing:'Custos',terminal:'Terminal'};
let currentView='overview';let latest={};const samples=[];let catalogue=[];let category='Todos';
function text(id,value){const e=$(id);if(e)e.textContent=value===null||value===undefined||value===''?'—':String(value)}
function bytes(value){const n=Number(value);if(!Number.isFinite(n)||n<0)return '—';if(!n)return '0 B';const names=['B','KiB','MiB','GiB','TiB','PiB'];const idx=Math.min(5,Math.floor(Math.log(n)/Math.log(1024)));return (n/1024**idx).toFixed(idx?1:0)+' '+names[idx]}
function pct(v){return Number.isFinite(Number(v))&&v!==null&&v!==undefined?Math.round(Number(v))+'%':'—'}
function uptime(v){if(!Number.isFinite(Number(v))||v==null)return '—';let s=Math.floor(v),d=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60);return (d?d+' dia'+(d!==1?'s':'')+', ':'')+h+'h '+m+'min'}
function meter(id,p){const e=$(id);if(e)e.style.width=p==null||!Number.isFinite(+p)?'0%':Math.max(0,Math.min(100,+p))+'%'}
function node(tag,cls,val){const e=document.createElement(tag);if(cls)e.className=cls;if(val!==undefined&&val!==null)e.textContent=val;return e}
function cell(row,v,cls){row.append(node('td',cls||'',v===undefined||v===null||v===''?'—':String(v)))}
function emptyRow(body,cols,msg){body.replaceChildren();const tr=node('tr');const td=node('td','empty-cell',msg);td.colSpan=cols;tr.append(td);body.append(tr)}
function showView(view){const id=VIEW_NAMES[view]?view:'overview';currentView=id;['overview','catalog','billing','detail'].forEach(k=>{const p=$('page-'+k);p.classList.toggle('active-page',k===(['overview','catalog','billing'].includes(id)?id:'detail'))});
 document.querySelectorAll('[data-target]').forEach(el=>{if(el.matches('a')){el.classList.toggle('selected',el.dataset.target===id)}});
 if(!['overview','catalog','billing'].includes(id)){text('detail-title',VIEW_NAMES[id]);text('detail-description','Dados obtidos apenas da instância StorOS em execução. Funções administrativas ainda não liberadas.');renderDetail(id)}
 window.scrollTo({top:0,behavior:'smooth'});if(location.hash.slice(1)!==id)history.replaceState({},'', '#'+id)}
function bindNav(){document.querySelectorAll('[data-target]').forEach(el=>el.addEventListener('click',ev=>{ev.preventDefault();showView(el.dataset.target)}));const toggle=$('theme-toggle');toggle.addEventListener('click',()=>document.body.classList.toggle('soft-mode'));
 $('global-search-form').addEventListener('submit',ev=>{ev.preventDefault();const q=$('global-search').value.trim().toLowerCase();const entry=Object.entries(VIEW_NAMES).find(e=>e[1].toLowerCase().includes(q));if(entry&&q)showView(entry[0])});document.addEventListener('keydown',ev=>{if((ev.ctrlKey||ev.metaKey)&&ev.key.toLowerCase()==='k'){ev.preventDefault();$('global-search').focus()}});
 $('overview-app-filter').addEventListener('input',renderCatalogPreview);document.querySelectorAll('[data-category]').forEach(button=>button.addEventListener('click',()=>{category=button.dataset.category;document.querySelectorAll('[data-category]').forEach(b=>b.classList.toggle('active',b===button));renderCatalogPreview()}));$('identity-button').addEventListener('click',()=>showView('users'));
 window.addEventListener('hashchange',()=>showView(location.hash.slice(1)||'overview'));showView(location.hash.slice(1)||'overview')}
function renderSystem(d,o){text('hero-host',d.host);text('hero-uptime',uptime(d.uptime_seconds));const total=Number(d.ram_total_bytes)||0;const used=total-Math.max(0,Number(d.ram_available_bytes)||0);text('memory-value',total?pct(used/total*100):'—');text('memory-detail',total?bytes(used)+' / '+bytes(total):'Sem leitura de RAM');meter('memory-meter',total?100*used/total:null);
 const c=o&&o.cpu||{};text('cpu-value',pct(c.percent));text('cpu-detail',c.model?c.model+' · '+(c.logical_cores||'—')+' threads':'Sem leitura de CPU');
 if(c.percent!==null&&Number.isFinite(+c.percent)){samples.push(+c.percent);if(samples.length>55)samples.shift();drawChart()}
 const storage=o&&o.storage&&o.storage.root; text('storage-value',storage?pct(storage.percent):'—');text('storage-detail',storage?bytes(storage.used_bytes)+' / '+bytes(storage.total_bytes)+' ('+(o&&o.storage&&o.storage.root_mount||'/')+')':'Uso não disponível');meter('storage-meter',storage?storage.percent:null);
}
function drawChart(){const chart=$('cpu-chart-path');if(samples.length<2){text('cpu-chart-caption','Aguardando mais amostras reais');return}const pts=samples.map((n,i)=>(i/(Math.max(samples.length-1,1))*360).toFixed(1)+','+(63-Math.min(100,n)*.63).toFixed(1));chart.setAttribute('d','M'+pts.join(' L'));const mini=$('cpu-mini');mini.replaceChildren();const svg=document.createElementNS(NODE_SVG,'svg');svg.setAttribute('viewBox','0 0 360 63');svg.setAttribute('preserveAspectRatio','none');const path=document.createElementNS(NODE_SVG,'path');path.setAttribute('d','M'+pts.join(' L'));path.setAttribute('fill','none');path.setAttribute('stroke','#51e5b5');path.setAttribute('stroke-width','3');svg.append(path);mini.append(svg);text('cpu-chart-caption',samples.length+' leituras coletadas nesta sessão')}
function renderStorage(d){const b=$('overview-disks'),rows=d&&d.items||[];if(!d||!d.available||!rows.length){emptyRow(b,5,d&&d.available?'Nenhum disco detectado':'Inventário de discos indisponível');return}b.replaceChildren();rows.slice(0,6).forEach(v=>{const tr=node('tr');cell(tr,v.name);cell(tr,bytes(v.size_bytes));const td=node('td');if(v.usage&&v.usage.percent!==null){const u=node('span','usage',pct(v.usage.percent));const bar=node('span','usage-bar');const fill=node('span');fill.style.width=Math.min(100,v.usage.percent)+'%';if(v.usage.percent>=65)fill.classList.add('warn');bar.append(fill);td.append(u,bar)}else td.textContent='—';tr.append(td);cell(tr,v.filesystem);cell(tr,'Detectado');b.append(tr)})}
function renderContainers(d){const b=$('overview-containers');if(!d||!d.available){text('containers-value','—');text('apps-value','—');text('containers-detail','Docker sem permissão de leitura');text('apps-detail','Instalações não verificadas');emptyRow(b,5,'Dados de containers indisponíveis');return}const items=d.items||[];text('containers-value',items.length);text('containers-detail',items.length+' em execução');text('apps-value','—');text('apps-detail','Instalações não verificadas');if(!items.length)return emptyRow(b,5,'Nenhum container em execução');b.replaceChildren();items.slice(0,5).forEach(x=>{const tr=node('tr');cell(tr,x.name);cell(tr,x.image);cell(tr,x.status||'Em execução','state-ok');cell(tr,x.cpu_percent);cell(tr,x.memory);b.append(tr)})}
function renderVMs(d){const b=$('overview-vms');if(!d||!d.available){text('vms-value','—');text('vms-detail','libvirt indisponível');emptyRow(b,5,'Virtualização não integrada nesta instância');return}const a=d.items||[];text('vms-value',a.length);text('vms-detail',a.length+' identificada(s)');if(!a.length)return emptyRow(b,5,'Nenhuma VM identificada');b.replaceChildren();a.slice(0,4).forEach(x=>{const tr=node('tr');cell(tr,x.name);cell(tr,null);cell(tr,x.status==='listed'?'Identificada':x.status);cell(tr,null);cell(tr,null);b.append(tr)})}
function renderNetworks(d){const b=$('overview-networks');if(!d||!d.available)return emptyRow(b,4,'Interfaces de rede indisponíveis');const rows=d.interfaces||[];if(!rows.length)return emptyRow(b,4,'Nenhuma interface detectada');b.replaceChildren();rows.slice(0,5).forEach(x=>{const tr=node('tr');cell(tr,x.name+(x.primary?' (Principal)':''));cell(tr,x.ip);cell(tr,x.speed_mbps?x.speed_mbps>=1000?(x.speed_mbps/1000)+' Gbps':x.speed_mbps+' Mbps':null);cell(tr,x.state==='UP'?'Conectado':x.state,x.state==='UP'?'state-ok':'');b.append(tr)})}
function renderStacks(d){const b=$('overview-stacks');if(!d||!d.available)return b.replaceChildren(node('div','empty-card','Docker Compose sem acesso de leitura'));const rows=d.items||[];if(!rows.length)return b.replaceChildren(node('div','empty-card','Nenhuma stack identificada'));b.replaceChildren();rows.slice(0,4).forEach(x=>{const row=node('div','stack-row');const i=document.createElement('i');i.setAttribute('data-icon','folder');row.append(i,node('strong','',x.name||'—'),node('small','',x.status||'—'));b.append(row)});applyIcons(b)}
function appIcon(n){const k=String(n).toLowerCase();return k.includes('jellyfin')?'△':k.includes('grafana')?'◉':k.includes('nginx')?'N':k.includes('nextcloud')?'∞':k.includes('qbittorrent')?'qB':k.includes('home assistant')?'⌂':k.includes('gitea')?'G':k.includes('kuma')?'♥':k.slice(0,1).toUpperCase()}
function renderCatalogPreview(){const b=$('overview-catalog');if(!b)return;const q=$('overview-app-filter').value.trim().toLowerCase();const items=catalogue.filter(x=>(category==='Todos'||x.category===category)&&(x.name.toLowerCase().includes(q)||x.description.toLowerCase().includes(q)));b.replaceChildren();if(!items.length)return b.append(node('div','empty-card','Nenhum aplicativo encontrado'));items.forEach(x=>{const card=node('div','app-card');card.append(node('div','app-card-icon',appIcon(x.name)),node('div','app-card-name',x.name),node('div','app-card-desc',x.description));const action=node('button','', 'Ver Compose');action.type='button';action.addEventListener('click',()=>{showView('catalog');if(typeof previewCompose==='function')previewCompose(x.slug,x.name)});card.append(action);b.append(card)})}
function renderDetail(view){
 const box=$('detail-content');box.replaceChildren();const all=latest;
 let items=[];
 if(view==='storage')items=all.overview?.storage?.items?.map(x=>(x.name||'—')+' · '+bytes(x.size_bytes)+' · '+(x.filesystem||'—'))||[];
 if(view==='network')items=all.overview?.network?.interfaces?.map(x=>(x.name||'—')+' · '+(x.ip||'Sem IPv4')+' · '+(x.speed_mbps?x.speed_mbps+' Mbps':'—'))||[];
 if(view==='containers')items=all.containers?.items?.map(x=>x.name+' · '+(x.image||'—')+' · '+(x.status||'—'))||[];
 if(view==='compose')items=all.overview?.compose?.items?.map(x=>(x.name||'—')+' · '+(x.status||'—'))||[];
 if(view==='vms')items=all.vms?.items?.map(x=>x.name+' · '+(x.status||'—'))||[];
 if(items.length)items.forEach(line=>box.append(node('p','',line)));
 else box.append(node('p','detail-empty','—  Nenhum dado verificado disponível para este módulo.'));
 box.append(node('p','','Comandos de criação, exclusão, administração e instalação permanecem desativados nesta prévia.'));
}
async function getJSON(path){const control=new AbortController();const timer=setTimeout(()=>control.abort(),7500);try{const response=await fetch(path,{cache:'no-store',signal:control.signal});if(!response.ok)throw Error('HTTP '+response.status);return await response.json()}finally{clearTimeout(timer)}}
async function refresh(){const paths=[['status','/api/status'],['overview','/api/overview'],['disks','/api/disks'],['containers','/api/containers'],['vms','/api/vms'],['catalog','/api/apps/catalog']];const res=await Promise.allSettled(paths.map(x=>getJSON(x[1])));res.forEach((item,i)=>{latest[paths[i][0]]=item.status==='fulfilled'?item.value:null});if(latest.status)renderSystem(latest.status,latest.overview);if(latest.overview){renderStorage(latest.overview.storage);renderNetworks(latest.overview.network);renderStacks(latest.overview.compose)}else{emptyRow($('overview-disks'),5,'Dados indisponíveis');emptyRow($('overview-networks'),4,'Dados indisponíveis')}
 renderContainers(latest.containers);renderVMs(latest.vms);if(latest.catalog&&Array.isArray(latest.catalog.items)){catalogue=latest.catalog.items;renderCatalogPreview()}if(!['overview','catalog','billing'].includes(currentView))renderDetail(currentView)}
applyIcons();bindNav();refresh();setInterval(()=>{if(!document.hidden)refresh()},15000);