import {createClient} from '@supabase/supabase-js';
import {unzipSync,zipSync,strFromU8,strToU8} from 'fflate';

const net = window.fetch.bind(window);
let client, user, config, currentCase;
const urls = new Set();
const gate = document.getElementById('access-gate');
const configKey = 'pericia.connection.v1';
const escapeHTML = text => String(text ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const message = text => { const el=document.getElementById('access-message'); if(el) el.textContent=text; };
const page = (title,body) => {gate.innerHTML=`<div class="access-brand">P <span>PERÍCIA</span></div><div class="eyebrow">ESPAÇO DE TRABALHO ONLINE</div><h1>${title}</h1>${body}<p id="access-message" role="status"></p><p class="access-foot">Documentos e registros privados · GitHub Pages + Supabase</p>`;};
const assertResult = result => {if(result.error)throw Error(result.error.message);return result.data;};
function validateConnection(value) {
  if(!value || !/^https:\/\/[a-z0-9-]+\.supabase\.co\/?$/.test(value.url) || typeof value.publishableKey!=='string') throw Error('Informe a URL HTTPS e a chave pública do seu projeto Supabase.');
  const key=value.publishableKey.trim();
  if(key.startsWith('sb_secret_'))throw Error('Use a chave publicável, nunca uma chave secreta.');
  if(!key.startsWith('sb_publishable_')) {
    let payload;try{payload=JSON.parse(atob(key.split('.')[1].replace(/-/g,'+').replace(/_/g,'/')));}catch{throw Error('Chave pública inválida.');}
    if(payload.role!=='anon')throw Error('Use somente a chave anon/publicável, nunca service_role.');
  }
  return {url:value.url.replace(/\/$/,''),publishableKey:key};
}
function setupPage(){
  page('Conectar o armazenamento privado',`<p>O endereço do sistema já está no GitHub Pages. Para ativar o login e guardar o acompanhamento entre dispositivos, conecte seu projeto gratuito Supabase.</p><ol><li>Crie um projeto no plano Free.</li><li>Execute a configuração SQL e crie seu usuário de acesso conforme o guia.</li><li>Informe abaixo a URL e a chave <b>pública</b> do projeto.</li></ol><p><a href="../blob/main/GUIA_GITHUB_PAGES.md" id="setup-guide" target="_blank" rel="noopener">Abrir passo a passo →</a></p><form id="connection-form"><label>URL do projeto<input name="url" type="url" placeholder="https://seuprojeto.supabase.co" required></label><label>Chave publicável (publishable ou anon)<input name="key" autocomplete="off" required placeholder="sb_publishable_…"></label><button class="primary">Conectar projeto</button></form><p class="access-help">Esta configuração contém somente dados públicos de conexão. Nunca informe chaves secretas ou service_role. Nenhum PDF foi publicado no GitHub.</p>`);
  document.getElementById('setup-guide').href='https://github.com/anielneto-source/pericia_teste/blob/main/GUIA_GITHUB_PAGES.md';
  document.getElementById('connection-form').onsubmit=async event=>{event.preventDefault();try{const form=new FormData(event.target);config=validateConnection({url:form.get('url'),publishableKey:form.get('key')});localStorage.setItem(configKey,JSON.stringify(config));await connect();}catch(error){message(error.message);}};
}
function loginPage(){
 page('Entrar no sistema',`<p>Acesse os documentos e o acompanhamento com seu e-mail e senha.</p><form id="access-form"><label>E-mail<input name="email" type="email" autocomplete="username" required></label><label>Senha<input name="password" type="password" autocomplete="current-password" required></label><button class="primary">Entrar</button></form><button id="change-connection" class="subtle-link">Alterar conexão do projeto</button>`);
 document.getElementById('access-form').onsubmit=async event=>{event.preventDefault();const button=event.target.querySelector('button');button.disabled=true;try{const form=new FormData(event.target);const result=assertResult(await client.auth.signInWithPassword({email:form.get('email'),password:form.get('password')}));user=result.user;await loadWorkspace();}catch{message('Não foi possível entrar. Confira o e-mail, a senha e se o usuário está ativo no Supabase.');button.disabled=false;}};
 document.getElementById('change-connection').onclick=()=>{localStorage.removeItem(configKey);setupPage();};
}
async function connect(){
 client=createClient(config.url,config.publishableKey,{auth:{persistSession:true,storage:sessionStorage,storageKey:'pericia.auth.'+new URL(config.url).hostname,autoRefreshToken:true,detectSessionInUrl:false},global:{fetch:net}});
 const {data,error}=await client.auth.getUser();
 if(error||!data.user){loginPage();return;}
 user=data.user;await loadWorkspace();
}
async function readCase(){
 return assertResult(await client.from('pericia_cases').select('state,documents,tree').eq('user_id',user.id).maybeSingle());
}
async function loadWorkspace(){
 try{currentCase=await readCase();if(!currentCase){importPage();return;}startApp();}
 catch(error){page('Concluir configuração',`<p>O login funcionou, mas o armazenamento ainda não está acessível. Execute o arquivo <b>deploy/supabase.sql</b> no SQL Editor do seu projeto e confira as políticas de acesso.</p><p id="setup-error"></p><button class="primary" id="retry-setup">Tentar novamente</button>`);document.getElementById('setup-error').textContent=error.message;document.getElementById('retry-setup').onclick=loadWorkspace;}
}
function parsePackage(bytes){
 let total=0,count=0;
 const entries=unzipSync(bytes,{filter:entry=>{total+=entry.originalSize;count++;if(total>300*1024*1024||count>10000)throw Error('Pacote muito grande.');return true;}});
 const names=Object.keys(entries);
 for(const name of names){if(name.startsWith('/')||name.includes('\\')||name.includes(':')||name.split('/').includes('..')||(name!=='state.json'&&!name.startsWith('Pericia_5090332/')))throw Error('Estrutura do pacote inválida.');}
 const state=JSON.parse(strFromU8(entries['state.json']));
 const documents=JSON.parse(strFromU8(entries['Pericia_5090332/00_Gestao_e_indice/inventario.json']));
 if(!['tasks','questions','stages','activity'].every(key=>Array.isArray(state[key]))||typeof state.case!=='string'||typeof state.notes!=='string'||!Array.isArray(documents))throw Error('Acompanhamento inválido.');
 for(const doc of documents)for(const key of ['path','textPath']){if(!entries['Pericia_5090332/'+doc[key]])throw Error('Documento ausente no pacote.');}
 const files=names.filter(name=>name.startsWith('Pericia_5090332/')&&!name.endsWith('/')).map(name=>({path:name.slice('Pericia_5090332/'.length),data:entries[name]}));
 const tree=new Map();
 function folder(path){if(!path)return;tree.set(path,{path,name:path.split('/').pop(),directory:true,size:0});folder(path.split('/').slice(0,-1).join('/'));}
 for(const s of state.stages)folder(s.folder);
 for(const file of files){folder(file.path.split('/').slice(0,-1).join('/'));tree.set(file.path,{path:file.path,name:file.path.split('/').pop(),directory:false,size:file.data.length});}
 return {state,documents,files,tree:[...tree.values()].sort((a,b)=>a.path.localeCompare(b.path))};
}
function importPage(){
 page('Importar sua perícia',`<p>Entre os dispositivos, seus registros ficarão na sua conta privada. Importe o pacote gerado no computador para iniciar.</p><form id="package-form"><label>Pacote privado da perícia (ZIP)<input name="package" type="file" accept=".zip" required></label><button class="primary">Importar documentos e plano</button></form><button id="import-logout" class="subtle-link">Sair da conta</button><p class="access-help">Use o arquivo Pacote_privado_pericia.zip da pasta principal do projeto. O conteúdo será enviado somente ao seu projeto Supabase autenticado.</p>`);
 document.getElementById('import-logout').onclick=logout;
 document.getElementById('package-form').onsubmit=async event=>{
  event.preventDefault();const button=event.target.querySelector('button');button.disabled=true;
  try{
   const file=event.target.elements.package.files[0];if(file.size>100*1024*1024)throw Error('O pacote deve ter até 100 MB.');
   message('Conferindo pacote…');const parsed=parsePackage(new Uint8Array(await file.arrayBuffer()));
   if(await readCase())throw Error('Já existe um acompanhamento nesta conta. Recarregue a página.');
   const importId=crypto.randomUUID();let done=0;
   // Pasta exclusiva por tentativa: nenhuma importação sobrescreve arquivos ativos.
   for(const entry of parsed.files){
    assertResult(await client.storage.from('pericia-private').upload(`${user.id}/${importId}/${entry.path}`,entry.data,{contentType:mime(entry.path),upsert:false}));
    done++;message(`Enviando arquivo ${done} de ${parsed.files.length}…`);
   }
   const tree=parsed.tree.map(entry=>({...entry,storagePrefix:importId}));
   assertResult(await client.from('pericia_cases').insert({user_id:user.id,state:parsed.state,documents:parsed.documents,tree}));
   location.reload();
  }catch(error){message('Importação não concluída: '+error.message);button.disabled=false;}
 };
}
const mime=path=>{const ext=path.split('.').pop().toLowerCase();return {pdf:'application/pdf',png:'image/png',jpg:'image/jpeg',jpeg:'image/jpeg',webp:'image/webp',txt:'text/plain;charset=utf-8',md:'text/plain;charset=utf-8',json:'application/json'}[ext]||'application/octet-stream';};
async function getFile(path){
 const record=currentCase.tree.find(entry=>!entry.directory&&entry.path===path);
 if(!record)throw Error('Arquivo não encontrado no índice privado.');
 return assertResult(await client.storage.from('pericia-private').download(`${user.id}/${record.storagePrefix}/${path}`));
}
async function logout(){await client.auth.signOut();for(const url of urls)URL.revokeObjectURL(url);location.reload();}
function saveBlob(blob,name){const url=URL.createObjectURL(blob);const anchor=document.createElement('a');anchor.href=url;anchor.download=name;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}
async function downloadBackup(complete){
 currentCase=await readCase();
 if(!complete){saveBlob(new Blob([JSON.stringify(currentCase.state,null,2)],{type:'application/json'}),'plano-pericia-backup.json');return;}
 const entries={'state.json':strToU8(JSON.stringify(currentCase.state,null,2))};
 for(const record of currentCase.tree.filter(e=>!e.directory)){const blob=await getFile(record.path);entries['Pericia_5090332/'+record.path]=new Uint8Array(await blob.arrayBuffer());}
 saveBlob(new Blob([zipSync(entries)],{type:'application/zip'}),'pericia-backup-completo.zip');
}
function startApp(){
 gate.hidden=true;document.body.classList.add('app-ready');
 window.fetch=async(resource,options={})=>{
  const url=new URL(typeof resource==='string'?resource:resource.url,location.href);
  if(url.origin!==location.origin||!url.pathname.startsWith('/api/'))return net(resource,options);
  try{
   let data;
   if(url.pathname==='/api/update'){
    const update=JSON.parse(options.body);data=assertResult(await client.rpc('pericia_update',{kind:update.kind,item_id:update.id??null,fields:update.fields}));currentCase.state=data;
   }else{
    const fresh=await readCase();if(!fresh)throw Error('Acompanhamento não encontrado.');currentCase=fresh;
    if(url.pathname==='/api/state')data=fresh.state;
    else if(url.pathname==='/api/documents')data=fresh.documents;
    else if(url.pathname==='/api/tree')data=fresh.tree;
    else throw Error('Rota não disponível.');
   }
   return new Response(JSON.stringify(data),{status:200,headers:{'Content-Type':'application/json'}});
  }catch(error){return new Response(JSON.stringify({error:error.message}),{status:400,headers:{'Content-Type':'application/json'}});}
 };
 const label=document.querySelector('.case-number');label.textContent=currentCase.state.case;
 const badge=document.querySelector('.local-badge');badge.textContent='● SESSÃO PRIVADA';
 const side=document.querySelector('.sidebar-bottom');side.innerHTML='<span class="dot"></span> Dados privados sincronizados<div>Salvos na sua conta online</div><button class="subtle-link" id="complete-backup">↓ Backup completo</button><button class="primary" id="sign-out">Sair</button>';
 document.getElementById('complete-backup').onclick=async()=>{try{await downloadBackup(true);}catch(error){alert('Não foi possível concluir o backup: '+error.message);}};
 document.getElementById('sign-out').onclick=logout;
 document.addEventListener('click',async event=>{
  const anchor=event.target.closest('a');if(!anchor)return;const url=new URL(anchor.href,location.href);
  if(url.origin!==location.origin)return;
  if(url.pathname==='/api/backup'){event.preventDefault();try{await downloadBackup(false);}catch(error){alert(error.message);}return;}
  if(url.pathname.startsWith('/files/')){
   event.preventDefault();const tab=window.open('about:blank','_blank');if(tab)tab.opener=null;
   try{const path=decodeURIComponent(url.pathname.slice('/files/'.length));const data=await getFile(path);const blob=new Blob([data],{type:mime(path)});const link=URL.createObjectURL(blob);urls.add(link);if(tab)tab.location.replace(link);else saveBlob(blob,path.split('/').pop());}
   catch(error){if(tab)tab.close();alert('Não foi possível abrir o arquivo: '+error.message);}
  }
 });
 const script=document.createElement('script');script.src='app.js';document.body.append(script);
}
async function boot(){
 try{const response=await net('config.json',{cache:'no-store'});const shared=await response.json();const saved=JSON.parse(localStorage.getItem(configKey)||'null');config=validateConnection(shared.url?shared:saved);await connect();}
 catch{setupPage();}
}
boot();
