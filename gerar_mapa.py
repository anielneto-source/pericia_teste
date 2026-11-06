from pathlib import Path
import openpyxl, json, collections, math, html, zipfile, urllib.request, gzip
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'docs'
OUT.mkdir(exist_ok=True)
(OUT/'vendor').mkdir(exist_ok=True)
(OUT/'icones').mkdir(exist_ok=True)
w = openpyxl.load_workbook(ROOT/'Planilha_Consolidada_Drenagem_COM_RUAS.xlsx', read_only=True, data_only=True)
it = iter(w['Resultados'].values)
headers = next(it)
features, rejected = [], []
for rownum, row in enumerate(it, 2):
    p = {str(k): v.isoformat() if hasattr(v,'isoformat') else v for k,v in zip(headers,row)}
    raw = str(p.get('nombre_falla','')).casefold().strip()
    if raw not in ('tampa de bueiro','boca de lobo'):
        rejected.append({'linha':rownum,'motivo':'Tipo não selecionado'}); continue
    try:
        lon,lat = float(p['longitud']),float(p['latitud'])
        assert math.isfinite(lon) and math.isfinite(lat) and -180<=lon<=180 and -90<=lat<=90
    except (ValueError,TypeError,AssertionError):
        rejected.append({'linha':rownum,'motivo':'Coordenada inválida'}); continue
    p['tipo'] = 'Tampa de Bueiro' if raw.startswith('tampa') else 'Boca de Lobo'
    p['linha_planilha'] = rownum
    features.append({'type':'Feature','id':rownum,'geometry':{'type':'Point','coordinates':[lon,lat]},'properties':p})
data={'type':'FeatureCollection','features':features}
(OUT/'drenagem.geojson').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
with gzip.open(OUT/'drenagem.geojson.gz','wb',compresslevel=9) as stream:stream.write((OUT/'drenagem.geojson').read_bytes())
counts=collections.Counter(f['properties']['tipo'] for f in features)
report={'origem':'Planilha_Consolidada_Drenagem_COM_RUAS.xlsx','aba':'Resultados','coluna_tipo':'nombre_falla','coordenadas':'longitud / latitud; interpretadas como longitude/latitude WGS84, sem reprojeção','registros_exportados':len(features),'por_tipo':dict(counts),'excluidos':rejected,'coordenadas_repetidas':len(features)-len(set(tuple(f['geometry']['coordinates']) for f in features)),'nota':'Registros coincidentes preservados; caracteres de substituição já existentes na planilha são preservados.'}
(OUT/'relatorio.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
shapes={'Tampa de Bueiro':'<circle cx="24" cy="24" r="19"/><path d="M12 18h24M10 25h28M13 32h22"/>','Boca de Lobo':'<rect x="5" y="10" width="38" height="29" rx="4"/><path d="M13 14v21m8-21v21m8-21v21m8-21v21"/>'}
colors={'Tampa de Bueiro':'#14b8a6','Boca de Lobo':'#f59e0b'}
for typ,shape in shapes.items():
    name='tampa' if typ.startswith('Tampa') else 'boca'
    (OUT/'icones'/f'{name}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><title>{typ}</title><g fill="{colors[typ]}" stroke="#102b40" stroke-width="3">{shape}</g></svg>',encoding='utf-8')
    im=Image.new('RGBA',(64,64)); d=ImageDraw.Draw(im)
    if name=='tampa':
        d.ellipse((5,5,59,59),fill=colors[typ],outline='#102b40',width=4)
        for y in (22,32,42):d.line((17,y,47,y),fill='#102b40',width=4)
    else:
        d.rounded_rectangle((4,12,60,53),radius=5,fill=colors[typ],outline='#102b40',width=4)
        for x in (16,26,37,48):d.line((x,18,x,47),fill='#102b40',width=4)
    im.save(OUT/'icones'/f'{name}.png')
# Google Earth: PNG symbols embedded because SVG support varies by client.
ns='http://www.opengis.net/kml/2.2'; ET.register_namespace('',ns)
def el(parent,tag,text=None,**attrs):
    child=ET.SubElement(parent,'{'+ns+'}'+tag,attrs)
    if text is not None: child.text=str(text)
    return child
kml=ET.Element('{'+ns+'}kml'); doc=el(kml,'Document');el(doc,'name','Drenagem • Aparecida de Goiânia')
for typ in shapes:
    key='tampa' if typ.startswith('Tampa') else 'boca'
    st=el(doc,'Style',id=key);icon=el(el(st,'IconStyle'),'Icon');el(icon,'href',f'icones/{key}.png')
    folder=el(doc,'Folder');el(folder,'name',f'{typ} ({counts[typ]})')
    for f in features:
        p=f['properties']
        if p['tipo']!=typ:continue
        mark=el(folder,'Placemark');el(mark,'name',f"{typ} • linha {p['linha_planilha']}");el(mark,'styleUrl','#'+key)
        desc='<table>'+''.join(f'<tr><th>{html.escape(k)}</th><td>{html.escape(str(v))}</td></tr>' for k,v in p.items() if v is not None)+'</table>'
        photo=p.get('Foto')
        if isinstance(photo,str) and photo.startswith('https://'):desc+=f'<p><a href="{html.escape(photo,quote=True)}">Abrir fotografia</a></p><img width="420" src="{html.escape(photo,quote=True)}"/>'
        el(mark,'description',desc)
        ext=el(mark,'ExtendedData')
        for k,v in p.items():
            if v is not None:el(el(ext,'Data',name=k),'value',v)
        lon,lat=f['geometry']['coordinates'];el(el(mark,'Point'),'coordinates',f'{lon},{lat},0')
ET.ElementTree(kml).write(OUT/'drenagem.kml',encoding='utf-8',xml_declaration=True)
with zipfile.ZipFile(OUT/'drenagem_google_earth.kmz','w',zipfile.ZIP_DEFLATED) as z:
    z.write(OUT/'drenagem.kml','doc.kml')
    for p in (OUT/'icones').glob('*.png'):z.write(p,'icones/'+p.name)
# Standalone SVG: clickable projected points and a persistent information panel.
lons=[f['geometry']['coordinates'][0] for f in features]; lats=[f['geometry']['coordinates'][1] for f in features]
lo,hi=min(lons),max(lons); la,ha=min(lats),max(lats)
scale=min(1120/((hi-lo)*math.cos(math.radians((la+ha)/2))),880/(ha-la))
points=[]
for f in features:
    lon,lat=f['geometry']['coordinates']; p=f['properties'];x=40+(lon-lo)*math.cos(math.radians((la+ha)/2))*scale;y=100+(ha-lat)*scale
    desc='\n'.join(f'{k}: {v}' for k,v in p.items() if v is not None)
    points.append(f'<circle tabindex="0" role="button" aria-label="{html.escape(p["tipo"])} linha {p["linha_planilha"]}" cx="{x:.3f}" cy="{y:.3f}" r="2.4" fill="{colors[p["tipo"]]}" data-info="{html.escape(desc,quote=True)}"><title>{html.escape(desc)}</title></circle>')
svg='''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1050" viewBox="0 0 1600 1050"><rect width="1600" height="1050" fill="#102335"/><g fill="#fff" font-family="Arial"><text x="40" y="40" font-size="26">Drenagem · Aparecida de Goiânia</text><text x="40" y="70" font-size="15">Turquesa: tampa de bueiro · Âmbar: boca de lobo · Clique ou passe o mouse nos pontos</text></g>'''+''.join(points)+'''<rect x="1180" y="90" width="410" height="940" rx="10" fill="#fff"/><text x="1195" y="115" font-family="Arial" font-size="12" id="info">Selecione um ponto. Use zoom do navegador para ampliar.</text><script><![CDATA[function show(e){let s=e.target.getAttribute('data-info');if(!s)return;let t=document.getElementById('info');t.textContent='';let y=0;s.split('\n').forEach(line=>{for(let i=0;i<line.length;i+=52){let a=document.createElementNS('http://www.w3.org/2000/svg','tspan');a.setAttribute('x',1195);a.setAttribute('dy',y++?17:0);a.textContent=line.slice(i,i+52);t.appendChild(a);}});}document.addEventListener('click',show);document.addEventListener('keydown',e=>{if(e.key==='Enter')show(e)});]]></script></svg>'''
start=svg.index('<text x="1195"')
svg=svg[:start]+'''<foreignObject x="1190" y="100" width="390" height="920"><div xmlns="http://www.w3.org/1999/xhtml" style="height:900px;overflow:auto;font:12px Arial;white-space:pre-wrap;overflow-wrap:anywhere;padding:8px" id="info">Selecione um ponto. Use o zoom do navegador para ampliar. A ficha pode ser rolada.</div></foreignObject><script><![CDATA[function show(e){let s=e.target.getAttribute('data-info');if(s)document.getElementById('info').textContent=s;}document.addEventListener('click',show);document.addEventListener('keydown',e=>{if(e.key==='Enter')show(e)});]]></script></svg>'''
(OUT/'pontos_interativos.svg').write_text(svg,encoding='utf-8')
assets={'leaflet.js':'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js','leaflet.css':'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css','leaflet.markercluster.js':'https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js','MarkerCluster.css':'https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css','MarkerCluster.Default.css':'https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css'}
for name,url in assets.items():
    if not (OUT/'vendor'/name).exists():urllib.request.urlretrieve(url,OUT/'vendor'/name)
print(json.dumps(report,ensure_ascii=False,indent=2))
