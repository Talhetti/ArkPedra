#!/usr/bin/env python3
"""Gera dashboard HTML estático com os dados incorporados."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "leads_londrina.json"
OUT = ROOT / "outputs"


def main() -> None:
    leads = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "leads_londrina.json").write_text(json.dumps(leads, ensure_ascii=False, indent=2), encoding="utf-8")
    template = r'''<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="Dashboard de prospecção B2B em Londrina/PR">
  <title>Radar de Leads — Londrina</title>
  <style>
    :root{--ink:#13212b;--muted:#667782;--paper:#f4f7f8;--card:#fff;--line:#dce5e8;--navy:#123b4a;--teal:#0e7c79;--mint:#dff3ef;--amber:#f4b942;--red:#c8553d;--blue:#3e6fa8;--shadow:0 10px 28px rgba(18,59,74,.08)}
    *{box-sizing:border-box} body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.45 Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
    button,input,select,textarea{font:inherit} a{color:var(--teal);text-decoration:none} a:hover{text-decoration:underline}
    .shell{max-width:1500px;margin:auto;padding:28px}.hero{background:linear-gradient(135deg,#0d3340,#0f5f63);color:#fff;border-radius:24px;padding:28px 32px;box-shadow:var(--shadow);position:relative;overflow:hidden}
    .hero:after{content:"";position:absolute;width:340px;height:340px;border:62px solid rgba(255,255,255,.06);border-radius:50%;right:-120px;top:-170px}.eyebrow{text-transform:uppercase;letter-spacing:.16em;font-weight:800;font-size:11px;color:#aee5dc}
    h1{font-size:clamp(28px,4vw,48px);line-height:1.02;margin:7px 0 10px;max-width:720px}.hero p{margin:0;color:#d7e9e8;max-width:820px}.hero-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}
    .btn{border:0;border-radius:10px;padding:10px 14px;font-weight:750;cursor:pointer;background:#fff;color:var(--navy)}.btn.secondary{background:rgba(255,255,255,.12);color:#fff;border:1px solid rgba(255,255,255,.25)}
    .kpis{display:grid;grid-template-columns:repeat(5,minmax(150px,1fr));gap:12px;margin:18px 0}.kpi{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:17px;box-shadow:var(--shadow)}.kpi .label{color:var(--muted);font-size:12px;font-weight:700}.kpi strong{display:block;font-size:30px;line-height:1.1;margin-top:8px}.kpi small{display:block;color:var(--muted);margin-top:5px}
    .niche-strip{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 20px}.chip{background:#e8eff1;color:#29444e;border-radius:99px;padding:7px 11px;font-size:12px;font-weight:750}
    .panel{background:var(--card);border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow);margin:16px 0;overflow:hidden}.panel-head{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:20px 22px;border-bottom:1px solid var(--line)}.panel h2{font-size:19px;margin:0}.panel-head p{margin:4px 0 0;color:var(--muted);font-size:12px}
    .filters{display:grid;grid-template-columns:2fr repeat(4,minmax(150px,1fr));gap:10px;padding:16px 22px;border-bottom:1px solid var(--line)}.field{display:flex;flex-direction:column;gap:5px}.field label{font-size:11px;font-weight:800;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}.field input,.field select{border:1px solid #cad7db;border-radius:9px;padding:9px 10px;background:#fff;color:var(--ink);min-width:0}
    .table-wrap{overflow:auto}.leads{width:100%;border-collapse:collapse;min-width:1080px}.leads th{position:sticky;top:0;background:#eef4f5;color:#48606a;font-size:11px;text-transform:uppercase;letter-spacing:.04em;text-align:left;padding:11px 12px;border-bottom:1px solid var(--line)}.leads td{padding:12px;border-bottom:1px solid #edf1f2;vertical-align:middle}.leads tbody tr{cursor:pointer}.leads tbody tr:hover{background:#f7fbfb}.name{font-weight:800}.sub{color:var(--muted);font-size:12px;margin-top:2px}.link-pill{display:inline-flex;border:1px solid #c9dedc;background:#f2fbf9;border-radius:8px;padding:4px 7px;font-weight:700;font-size:11px;margin:1px}.score{display:inline-grid;place-items:center;width:42px;height:42px;border-radius:50%;font-weight:900;background:#e8f4f1;color:#075f5c}.score.high{background:#fce9bf;color:#7c5200}.priority{display:inline-block;border-radius:99px;padding:5px 8px;font-size:11px;font-weight:850;white-space:nowrap}.p-a{background:#fde2dd;color:#8c2f20}.p-b{background:#fff0c9;color:#7b5700}.p-c{background:#dfeaf7;color:#2d5680}.p-d{background:#e8edef;color:#53646c}.status-select{max-width:145px;border:1px solid #cad7db;border-radius:8px;padding:6px;background:white}
    .pager{display:flex;justify-content:space-between;align-items:center;padding:14px 22px;color:var(--muted)}.pager button{border:1px solid var(--line);background:#fff;border-radius:8px;padding:7px 11px;cursor:pointer}.pager button:disabled{opacity:.4;cursor:not-allowed}
    .charts{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;padding:20px}.chart{border:1px solid var(--line);border-radius:14px;padding:15px;min-height:240px}.chart h3{margin:0 0 14px;font-size:14px}.bar-row{margin:10px 0}.bar-label{display:flex;justify-content:space-between;gap:8px;font-size:11px;color:#50646d;margin-bottom:4px}.track{height:9px;background:#e9eff1;border-radius:99px;overflow:hidden}.fill{height:100%;border-radius:99px;background:var(--teal)}
    .map-grid{display:grid;grid-template-columns:1.25fr .75fr;gap:16px;padding:20px}.coord-map{position:relative;min-height:380px;border-radius:15px;background:linear-gradient(155deg,#e2f0ec,#eef5f6);border:1px solid #cbdcdd;overflow:hidden}.coord-map:before{content:"Coordenadas verificadas — referência espacial relativa";position:absolute;left:14px;top:12px;color:#526a70;font-size:11px;font-weight:800}.dot{position:absolute;width:13px;height:13px;border-radius:50%;background:var(--red);border:2px solid white;box-shadow:0 1px 5px #6f8b8b;transform:translate(-50%,-50%);cursor:pointer}.dot:hover{width:18px;height:18px;z-index:3}.map-list{max-height:380px;overflow:auto}.map-item{padding:10px 2px;border-bottom:1px solid var(--line)}.map-item b{display:block}.map-item span{color:var(--muted);font-size:12px}
    .drawer{position:fixed;inset:0;background:rgba(6,24,31,.48);display:none;z-index:20}.drawer.open{display:block}.drawer-card{position:absolute;right:0;top:0;bottom:0;width:min(720px,94vw);background:white;padding:28px;overflow:auto;box-shadow:-20px 0 50px rgba(0,0,0,.18)}.drawer-top{display:flex;justify-content:space-between;gap:12px}.close{border:0;background:#edf3f4;width:36px;height:36px;border-radius:50%;cursor:pointer}.detail-title{font-size:26px;margin:3px 0}.detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:18px 0}.detail-box{border:1px solid var(--line);border-radius:12px;padding:13px}.detail-box label{font-size:10px;text-transform:uppercase;color:var(--muted);font-weight:850;letter-spacing:.05em;display:block;margin-bottom:5px}.wide{grid-column:1/-1}.detail-actions{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}.note-area{width:100%;min-height:90px;border:1px solid #cad7db;border-radius:10px;padding:10px}.sources{word-break:break-word;margin:0;padding-left:18px}.sources li{margin:6px 0}.foot{color:var(--muted);font-size:12px;text-align:center;padding:20px}
    .empty{padding:36px;text-align:center;color:var(--muted)}
    @media(max-width:1050px){.kpis{grid-template-columns:repeat(3,1fr)}.charts{grid-template-columns:repeat(2,1fr)}.filters{grid-template-columns:repeat(2,1fr)}.field:first-child{grid-column:1/-1}.map-grid{grid-template-columns:1fr}}
    @media(max-width:650px){.shell{padding:12px}.hero{padding:23px 20px;border-radius:18px}.kpis{grid-template-columns:1fr 1fr}.kpi:last-child{grid-column:1/-1}.charts{grid-template-columns:1fr}.filters{grid-template-columns:1fr}.field:first-child{grid-column:auto}.panel-head{align-items:flex-start}.detail-grid{grid-template-columns:1fr}.wide{grid-column:auto}}
  </style>
</head>
<body>
<main class="shell">
  <section class="hero">
    <div class="eyebrow">Prospecção B2B · Londrina/PR</div>
    <h1>Radar de oportunidades digitais</h1>
    <p>Base pública verificada em 18/10/2026. O score não presume ausência quando a informação não pôde ser confirmada.</p>
    <div class="hero-actions"><button class="btn" id="exportCsv">Exportar CSV</button><button class="btn secondary" id="exportJson">Exportar JSON</button><button class="btn secondary" id="resetCrm">Limpar acompanhamento local</button></div>
  </section>
  <section class="kpis" id="kpis"></section>
  <div class="niche-strip" id="nicheStrip"></div>

  <section class="panel">
    <div class="panel-head"><div><h2>Leads pesquisados</h2><p>Pesquise, filtre, atualize o funil e abra um lead para ver evidências e recomendações.</p></div><div id="resultCount" class="chip"></div></div>
    <div class="filters">
      <div class="field"><label>Pesquisar</label><input id="search" placeholder="Nome, bairro ou telefone"></div>
      <div class="field"><label>Nicho</label><select id="niche"><option value="">Todos</option></select></div>
      <div class="field"><label>Prioridade</label><select id="priority"><option value="">Todas</option><option>A</option><option>B</option><option>C</option><option>D</option></select></div>
      <div class="field"><label>Presença digital</label><select id="presence"><option value="">Todas</option><option>SEM SITE CONFIRMADO</option><option>SITE CONFIRMADO</option><option>INCOMPLETA</option><option>NÃO IDENTIFICADA</option></select></div>
      <div class="field"><label>Ordenação</label><select id="sort"><option value="scoreDesc">Maior score</option><option value="scoreAsc">Menor score</option><option value="name">Nome A–Z</option></select></div>
    </div>
    <div class="table-wrap"><table class="leads"><thead><tr><th>Empresa</th><th>Nicho</th><th>Bairro</th><th>Telefone</th><th>Presença</th><th>Links</th><th>Score</th><th>Prioridade</th><th>Status comercial</th></tr></thead><tbody id="leadRows"></tbody></table></div>
    <div class="pager"><span id="pageInfo"></span><div><button id="prev">Anterior</button> <button id="next">Próxima</button></div></div>
  </section>

  <section class="panel"><div class="panel-head"><div><h2>Distribuições</h2><p>Visão compacta da base e do funil salvo neste navegador.</p></div></div><div class="charts" id="charts"></div></section>

  <section class="panel"><div class="panel-head"><div><h2>Localização</h2><p>Somente leads com latitude e longitude presentes na fonte. Os demais mantêm link individual para o Google Maps.</p></div></div><div class="map-grid"><div class="coord-map" id="coordMap"></div><div class="map-list" id="mapList"></div></div></section>
  <div class="foot">Dados públicos para prospecção comercial. Confirme informações antes do contato. Alterações de funil ficam apenas no localStorage e não atualizam o Excel.</div>
</main>

<aside class="drawer" id="drawer" aria-hidden="true"><div class="drawer-card"><div class="drawer-top"><div><div class="eyebrow" style="color:var(--teal)">Detalhes do lead</div><h2 class="detail-title" id="detailName"></h2><div id="detailMeta"></div></div><button class="close" id="close" aria-label="Fechar">×</button></div><div id="detailBody"></div></div></aside>

<script>
const LEADS = __DATA__;
const STATUSES = ['não contatado','contatado','interessado','reunião','proposta enviada','fechado','perdido'];
const state={page:1,size:10};
const saved=JSON.parse(localStorage.getItem('leadCRM_v1')||'{}');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const priLetter=p=>(p.match(/Prioridade ([A-D])/)||[])[1]||'D';
const crm=l=>saved[l.id]||{status:l.commercial_status||'não contatado',notes:l.commercial_notes||''};
function persist(){localStorage.setItem('leadCRM_v1',JSON.stringify(saved));renderCharts()}
function counts(arr,key){return arr.reduce((a,x)=>(a[key(x)]=(a[key(x)]||0)+1,a),{})}
function renderSummary(){
  const priority=LEADS.filter(x=>x.score>=60).length, noSite=LEADS.filter(x=>x.site_status==='NÃO').length, incomplete=LEADS.filter(x=>x.presence_status==='INCOMPLETA').length;
  const cards=[['Empresas pesquisadas',LEADS.length,'100% em Londrina'],['Leads prioritários',priority,'Score ≥ 60'],['Sem site confirmado',noSite,'Ausência sustentada'],['Presença incompleta',incomplete,'Social isolada ou URL indisponível'],['Coordenadas verificadas',LEADS.filter(x=>Number.isFinite(x.latitude)&&Number.isFinite(x.longitude)).length,'Exibidas no mapa']];
  document.querySelector('#kpis').innerHTML=cards.map(x=>`<article class="kpi"><div class="label">${x[0]}</div><strong>${x[1]}</strong><small>${x[2]}</small></article>`).join('');
  const nc=counts(LEADS,x=>x.niche);document.querySelector('#nicheStrip').innerHTML=Object.entries(nc).map(([k,v])=>`<span class="chip">${esc(k)} · ${v}</span>`).join('');
}
function initFilters(){[...new Set(LEADS.map(x=>x.niche))].sort().forEach(n=>document.querySelector('#niche').insertAdjacentHTML('beforeend',`<option>${esc(n)}</option>`));['search','niche','priority','presence','sort'].forEach(id=>document.querySelector('#'+id).addEventListener(id==='search'?'input':'change',()=>{state.page=1;renderTable()}))}
function filtered(){
  const q=document.querySelector('#search').value.toLowerCase().trim(),n=document.querySelector('#niche').value,p=document.querySelector('#priority').value,pr=document.querySelector('#presence').value,s=document.querySelector('#sort').value;
  let a=LEADS.filter(x=>(!q||[x.name,x.bairro,x.phone].join(' ').toLowerCase().includes(q))&&(!n||x.niche===n)&&(!p||priLetter(x.priority)===p)&&(!pr||x.presence_status===pr));
  a.sort(s==='scoreAsc'?(a,b)=>a.score-b.score:s==='name'?(a,b)=>a.name.localeCompare(b.name,'pt-BR'):(a,b)=>b.score-a.score||a.name.localeCompare(b.name,'pt-BR'));return a;
}
function links(l){const a=[];a.push(`<a class="link-pill" href="${esc(l.maps_url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Mapa</a>`);if(l.website)a.push(`<a class="link-pill" href="${esc(l.website)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Site</a>`);if(l.instagram)a.push(`<a class="link-pill" href="${esc(l.instagram)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Instagram</a>`);if(l.facebook)a.push(`<a class="link-pill" href="${esc(l.facebook)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Facebook</a>`);return a.join('')}
function renderTable(){const a=filtered(),pages=Math.max(1,Math.ceil(a.length/state.size));state.page=Math.min(state.page,pages);const slice=a.slice((state.page-1)*state.size,state.page*state.size);document.querySelector('#resultCount').textContent=`${a.length} resultado${a.length===1?'':'s'}`;
  document.querySelector('#leadRows').innerHTML=slice.length?slice.map(l=>{const c=crm(l),letter=priLetter(l.priority);return `<tr data-id="${l.id}"><td><div class="name">${esc(l.name)}</div><div class="sub">${esc(l.address)}</div></td><td>${esc(l.niche)}</td><td>${esc(l.bairro)}</td><td>${esc(l.phone)}</td><td><b>${esc(l.presence_status)}</b><div class="sub">Site: ${esc(l.site_status)}</div></td><td>${links(l)}</td><td><span class="score ${l.score>=60?'high':''}">${l.score}</span></td><td><span class="priority p-${letter.toLowerCase()}">${esc(l.priority)}</span></td><td><select class="status-select" data-status="${l.id}" onclick="event.stopPropagation()">${STATUSES.map(s=>`<option ${c.status===s?'selected':''}>${s}</option>`).join('')}</select></td></tr>`}).join(''):`<tr><td colspan="9" class="empty">Nenhum lead corresponde aos filtros.</td></tr>`;
  document.querySelectorAll('tr[data-id]').forEach(r=>r.addEventListener('click',()=>openDetail(r.dataset.id)));document.querySelectorAll('[data-status]').forEach(s=>s.addEventListener('change',e=>{const id=e.target.dataset.status;saved[id]={...crm(LEADS.find(x=>x.id===id)),status:e.target.value};persist()}));document.querySelector('#pageInfo').textContent=`Página ${state.page} de ${pages}`;document.querySelector('#prev').disabled=state.page<=1;document.querySelector('#next').disabled=state.page>=pages;}
function barChart(title,data,color='#0e7c79'){const max=Math.max(...Object.values(data),1);return `<div class="chart"><h3>${title}</h3>${Object.entries(data).map(([k,v])=>`<div class="bar-row"><div class="bar-label"><span>${esc(k)}</span><b>${v}</b></div><div class="track"><div class="fill" style="width:${v/max*100}%;background:${color}"></div></div></div>`).join('')}</div>`}
function renderCharts(){const funnel={};STATUSES.forEach(s=>funnel[s]=0);LEADS.forEach(l=>funnel[crm(l).status]=(funnel[crm(l).status]||0)+1);document.querySelector('#charts').innerHTML=barChart('Distribuição por nicho',counts(LEADS,x=>x.niche))+barChart('Leads por prioridade',counts(LEADS,x=>priLetter(x.priority)),'#3e6fa8')+barChart('Presença digital',counts(LEADS,x=>x.presence_status),'#c8553d')+barChart('Funil comercial',funnel,'#f0a928')}
function renderMap(){const pts=LEADS.filter(x=>Number.isFinite(x.latitude)&&Number.isFinite(x.longitude));const lat=pts.map(x=>x.latitude),lng=pts.map(x=>x.longitude),minLat=Math.min(...lat),maxLat=Math.max(...lat),minLng=Math.min(...lng),maxLng=Math.max(...lng);document.querySelector('#coordMap').innerHTML=pts.map(p=>{const x=8+84*(p.longitude-minLng)/(maxLng-minLng||1),y=12+78*(maxLat-p.latitude)/(maxLat-minLat||1);return `<button class="dot" title="${esc(p.name)}" style="left:${x}%;top:${y}%" onclick="openDetail('${p.id}')"></button>`}).join('');document.querySelector('#mapList').innerHTML=pts.map(p=>`<div class="map-item"><b>${esc(p.name)}</b><span>${p.latitude.toFixed(5)}, ${p.longitude.toFixed(5)} · <a href="${esc(p.maps_url)}" target="_blank">abrir no mapa</a></span></div>`).join('')}
function val(label,value,wide=false){return `<div class="detail-box ${wide?'wide':''}"><label>${label}</label><div>${value||'<span class="sub">Não identificado</span>'}</div></div>`}
function openDetail(id){const l=LEADS.find(x=>x.id===id),c=crm(l);document.querySelector('#detailName').textContent=l.name;document.querySelector('#detailMeta').innerHTML=`<span class="priority p-${priLetter(l.priority).toLowerCase()}">${esc(l.priority)}</span> <span class="score ${l.score>=60?'high':''}" style="margin-left:8px">${l.score}</span>`;document.querySelector('#detailBody').innerHTML=`<div class="detail-actions">${links(l)}</div><div class="detail-grid">${val('Nicho',esc(l.niche))}${val('Bairro',esc(l.bairro))}${val('Endereço',esc(l.address),true)}${val('Telefone',esc(l.phone))}${val('WhatsApp',esc(l.whatsapp_status)+(l.whatsapp?' · '+esc(l.whatsapp):''))}${val('Site próprio',esc(l.site_status)+(l.website?' · '+`<a href="${esc(l.website)}" target="_blank">abrir</a>`:''))}${val('Teste técnico do site',esc(l.site_check_result)+(l.site_http_status?' · HTTP '+l.site_http_status:''))}${val('Instagram',l.instagram?`<a href="${esc(l.instagram)}" target="_blank">${esc(l.instagram)}</a>`:'')}${val('Facebook',l.facebook?`<a href="${esc(l.facebook)}" target="_blank">${esc(l.facebook)}</a>`:'')}${val('E-commerce',esc(l.ecommerce_status))}${val('Catálogo digital',esc(l.catalog_status))}${val('Agendamento online',esc(l.appointment_status))}${val('Serviços',esc(l.services),true)}${val('Fatos observados',esc(l.observed_facts),true)}${val('Oportunidades / hipóteses',esc(l.opportunities),true)}${val('Soluções recomendadas',esc(l.recommended_solutions),true)}${val('Abordagem sugerida',esc(l.suggested_approach),true)}${val('Justificativa do score',esc(l.score_justification),true)}${val('Verificação do site',esc(l.site_verification_note||''),true)}${val('Última verificação',esc(l.verified_at))}${val('Status comercial',`<select id="detailStatus" class="status-select">${STATUSES.map(s=>`<option ${c.status===s?'selected':''}>${s}</option>`).join('')}</select>`)}<div class="detail-box wide"><label>Observações comerciais (salvas neste navegador)</label><textarea class="note-area" id="detailNotes">${esc(c.notes)}</textarea></div><div class="detail-box wide"><label>Fontes consultadas</label><ul class="sources">${l.sources.map(s=>`<li><a href="${esc(s)}" target="_blank" rel="noopener">${esc(s)}</a></li>`).join('')}</ul></div></div>`;document.querySelector('#detailStatus').addEventListener('change',e=>{saved[id]={...crm(l),status:e.target.value};persist();renderTable()});document.querySelector('#detailNotes').addEventListener('input',e=>{saved[id]={...crm(l),notes:e.target.value};persist()});document.querySelector('#drawer').classList.add('open');document.querySelector('#drawer').setAttribute('aria-hidden','false')}
function closeDetail(){document.querySelector('#drawer').classList.remove('open');document.querySelector('#drawer').setAttribute('aria-hidden','true')}
function download(name,text,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
function exportData(){return LEADS.map(l=>({...l,commercial_status:crm(l).status,commercial_notes:crm(l).notes}))}
function csv(){const d=exportData(),keys=['name','niche','bairro','city','phone','website','instagram','score','priority','commercial_status','commercial_notes'];const q=v=>'"'+String(v??'').replace(/"/g,'""')+'"';return [keys.join(','),...d.map(x=>keys.map(k=>q(x[k])).join(','))].join('\n')}
document.querySelector('#prev').onclick=()=>{state.page--;renderTable()};document.querySelector('#next').onclick=()=>{state.page++;renderTable()};document.querySelector('#close').onclick=closeDetail;document.querySelector('#drawer').addEventListener('click',e=>{if(e.target.id==='drawer')closeDetail()});document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDetail()});document.querySelector('#exportCsv').onclick=()=>download('leads_londrina_atualizados.csv','\ufeff'+csv(),'text/csv;charset=utf-8');document.querySelector('#exportJson').onclick=()=>download('leads_londrina_atualizados.json',JSON.stringify(exportData(),null,2),'application/json');document.querySelector('#resetCrm').onclick=()=>{if(confirm('Limpar status e observações salvos neste navegador?')){Object.keys(saved).forEach(k=>delete saved[k]);persist();renderTable()}};
renderSummary();initFilters();renderTable();renderCharts();renderMap();
</script>
</body>
</html>'''
    html = template.replace("__DATA__", json.dumps(leads, ensure_ascii=False).replace("</", "<\\/"))
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(f"Dashboard gerado com {len(leads)} leads em {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
