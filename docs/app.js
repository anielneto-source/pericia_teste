'use strict';
const $=id=>document.getElementById(id),fmt=n=>n.toLocaleString('pt-BR');
const map=L.map('map',{preferCanvas:true}).setView([-16.82,-49.25],12);
const attribution='Tiles © Esri — Esri, Vantor, Maxar, Earthstar Geographics e GIS User Community';
const imagery=L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:20,maxNativeZoom:19,attribution});
const labels=L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{maxZoom:20,maxNativeZoom:19,attribution:'Rótulos © Esri, HERE, Garmin, © OpenStreetMap contributors'});
const roads=L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',{maxZoom:20,maxNativeZoom:19,attribution:'Vias © Esri, HERE, Garmin'});
const hybrid=L.layerGroup([imagery,roads,labels]).addTo(map);
const streets=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'});
L.control.layers({'Híbrido · satélite e vias':hybrid,'Ruas · OpenStreetMap':streets}).addTo(map);L.control.scale({imperial:false}).addTo(map);
let tileWarning=false;[imagery,labels,roads].forEach(layer=>layer.on('tileerror',()=>{if(!tileWarning){tileWarning=true;$('status').textContent='Base híbrida indisponível em parte. Use a opção Ruas no controle de camadas.';}}));
const cluster=L.markerClusterGroup({chunkedLoading:false,removeOutsideVisibleBounds:true,maxClusterRadius:55,showCoverageOnHover:false}).addTo(map);
L.control.layers(null,{'Pontos de drenagem':cluster},{collapsed:true}).addTo(map);
const icons=Object.fromEntries(['Tampa de Bueiro','Boca de Lobo'].map(t=>[t,L.divIcon({className:'symbol',html:`<img alt="${t}" src="icones/${t.startsWith('Tampa')?'tampa':'boca'}.svg">`,iconSize:[30,30],iconAnchor:[15,15],popupAnchor:[0,-14]})]));
function text(tag,value){const e=document.createElement(tag);e.textContent=value;return e;}
function popup(p){const box=document.createElement('div');box.append(text('h3',p.tipo),text('p',`Registro ${p.id_deterioro} · linha ${p.linha_planilha}`));
 const photo=p.Foto;if(typeof photo==='string'&&/^https?:\/\//i.test(photo)){const a=document.createElement('a');a.href=photo;a.target='_blank';a.rel='noopener noreferrer';a.textContent='Abrir fotografia';const img=document.createElement('img');img.className='photo';img.src=photo;img.loading='lazy';img.alt='Fotografia do registro';img.onerror=()=>{img.replaceWith(text('p','Fotografia indisponível no endereço de origem.'));};box.append(a,img);}
 const table=document.createElement('table');for(const [key,value] of Object.entries(p)){if(value===null||value==='')continue;const row=document.createElement('tr');row.append(text('th',key),text('td',String(value)));table.append(row);}box.append(table);return box;}
let features=[],selected=[],markers=[],searches=[];
function populate(id,key,emptyLabel){const values=[...new Set(features.map(f=>f.properties[key]).filter(v=>v!==null&&v!==''))].sort((a,b)=>String(a).localeCompare(String(b),'pt-BR'));for(const value of values){const o=document.createElement('option');o.value=String(value);o.textContent=String(value);$(id).append(o);}if(features.some(f=>!f.properties[key])){const o=document.createElement('option');o.value='__empty';o.textContent=emptyLabel;$(id).append(o);}}
function matches(p,key,value){return !value||(value==='__empty'?!p[key]:String(p[key])===value);}
function normalize(v){return String(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();}
function apply(){const types=[...document.querySelectorAll('[name=tipo]:checked')].map(e=>e.value),query=normalize($('busca').value.trim());selected=[];const visible=[];
 features.forEach((f,i)=>{const p=f.properties;if(types.includes(p.tipo)&&matches(p,'RUA_bairro_ful',$('bairro').value)&&matches(p,'gravedad',$('gravidade').value)&&matches(p,'RUA_logradouro',$('rua').value)&&(!query||searches[i].includes(query))){selected.push(f);visible.push(markers[i]);}});
 cluster.clearLayers();cluster.addLayers(visible);$('nT').textContent=fmt(selected.filter(f=>f.properties.tipo==='Tampa de Bueiro').length);$('nB').textContent=fmt(selected.filter(f=>f.properties.tipo==='Boca de Lobo').length);$('status').textContent=`${fmt(selected.length)} de ${fmt(features.length)} registros · contagens conforme filtros`;$('fit').disabled=!selected.length;$('export').disabled=!selected.length;}
function fit(){if(selected.length)map.fitBounds(L.latLngBounds(selected.map(f=>[f.geometry.coordinates[1],f.geometry.coordinates[0]])),{padding:[35,35],maxZoom:18});}
async function loadData(){
 if(typeof DecompressionStream!=='undefined'){
  try{const r=await fetch('drenagem.geojson.gz');if(!r.ok)throw Error(`HTTP ${r.status}`);return await new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).json();}catch(e){console.warn('Usando arquivo GeoJSON sem compacta??o.',e);}
 }
 const r=await fetch('drenagem.geojson');if(!r.ok)throw Error(`HTTP ${r.status}`);return r.json();
}
loadData().then(data=>{features=data.features;markers=features.map(f=>{const [lon,lat]=f.geometry.coordinates;const marker=L.marker([lat,lon],{icon:icons[f.properties.tipo],title:`${f.properties.tipo} · linha ${f.properties.linha_planilha}`});marker.bindPopup(()=>popup(f.properties),{maxWidth:370});return marker;});searches=features.map(f=>normalize(Object.values(f.properties).filter(v=>v!==null).join(' ')));populate('bairro','RUA_bairro_ful','Sem bairro');populate('rua','RUA_logradouro','Sem rua');populate('gravidade','gravedad','Sem gravidade');apply();fit();}).catch(e=>{$('status').textContent=`Erro ao carregar os dados: ${e.message}. Verifique sua conex?o e recarregue a p?gina.`;$('status').classList.add('error');});
document.querySelectorAll('select,[name=tipo]').forEach(e=>e.addEventListener('change',apply));let timer;$('busca').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(apply,250);});$('fit').onclick=fit;$('reset').onclick=()=>{document.querySelectorAll('select').forEach(e=>e.value='');document.querySelectorAll('[name=tipo]').forEach(e=>e.checked=true);$('busca').value='';apply();fit();};$('export').onclick=()=>{const blob=new Blob([JSON.stringify({type:'FeatureCollection',features:selected})],{type:'application/geo+json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='drenagem_filtrada.geojson';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
