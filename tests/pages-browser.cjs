// Teste da interface estática com a API Supabase simulada, sem enviar dados reais.
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8878/');await page.locator('#connection-form').waitFor();
  await page.locator('[name=url]').fill('https://pericia-test.supabase.co');await page.locator('[name=key]').fill('sb_secret_must_be_rejected');await page.locator('#connection-form button').click();
  if(!await page.locator('#connection-form').isVisible())throw Error('Secret key accepted');
  const uid='11111111-1111-4111-8111-111111111111';let record=null,uploads=0;
  await page.route('https://pericia-test.supabase.co/**',async route=>{
   const req=route.request(),url=new URL(req.url());const headers={'Content-Type':'application/json','Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'};
   if(req.method()==='OPTIONS')return route.fulfill({status:204,headers});
   const ok=data=>route.fulfill({status:200,headers,body:JSON.stringify(data)});
   if(url.pathname.endsWith('/token')){
    const now=Math.floor(Date.now()/1000);const jwt=[Buffer.from('{}').toString('base64url'),Buffer.from(JSON.stringify({sub:uid,exp:now+3600})).toString('base64url'),'test'].join('.');
    return ok({access_token:jwt,refresh_token:'fake-refresh',token_type:'bearer',expires_in:3600,user:{id:uid,email:'test@example.com',aud:'authenticated',role:'authenticated'}});
   }
   if(url.pathname.endsWith('/user'))return ok({id:uid,email:'test@example.com',aud:'authenticated'});
   if(url.pathname.endsWith('/logout'))return route.fulfill({status:204,headers});
   if(url.pathname==='/rest/v1/pericia_cases'){
    if(req.method()==='POST'){record=JSON.parse(req.postData());return route.fulfill({status:201,headers,body:''});}
    return ok(record?[record]:[]);
   }
   if(url.pathname==='/rest/v1/rpc/pericia_update'){
    const update=JSON.parse(req.postData());if(update.kind==='notes')record.state.notes=update.fields.notes;else Object.assign(record.state[update.kind].find(x=>x.id===update.item_id),update.fields);return ok(record.state);
   }
   if(url.pathname.startsWith('/storage/v1/object/')){
    if(req.method()==='POST'){uploads++;return ok({Key:'test-file'});}
    return route.fulfill({status:200,headers:{...headers,'Content-Type':'application/pdf'},body:Buffer.from('%PDF-test')});
   }
   throw Error('Unexpected request '+req.method()+' '+url.pathname);
  });
  await page.locator('[name=key]').fill('sb_publishable_test');await page.locator('#connection-form button').click();await page.locator('#access-form').waitFor();
  await page.locator('[name=email]').fill('test@example.com');await page.locator('[name=password]').fill('fake-password-only-for-test');await page.locator('#access-form button').click();await page.locator('#package-form').waitFor();
  const fixture=path.resolve(__dirname,'../../Pacote_privado_pericia.zip');
  if(!fs.existsSync(fixture))throw Error('Set up the local private ZIP fixture before this integration check.');
  await page.locator('[name=package]').setInputFiles(fixture);await page.locator('#package-form button').click();await page.locator('.hero').waitFor({timeout:60000});
  if(uploads<20||record.documents.length!==20)throw Error('Import incomplete');
  await page.locator('[data-view=plan]').click();await page.locator('[data-task="1"]').click();await page.locator('[name=notes]').fill('Pages test');await page.locator('#task-form button[type=submit]').click();await page.locator('#task-dialog').waitFor({state:'hidden'});
  if(record.state.tasks[0].notes!=='Pages test')throw Error('Save failed');
  await page.locator('[data-view=report]').click();await page.locator('.report-sheet').waitFor();if(await page.locator('.report-question').count()!==11)throw Error('Report failed');
  await page.setViewportSize({width:390,height:844});if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile overflow');
  await page.locator('#sign-out').click();await page.locator('#access-form').waitFor();
  if(errors.length)throw Error(errors.join());console.log('PASS: setup, rejected secret key, login, private ZIP import, transactional save, report, mobile and logout (mock backend).');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exit(1)});
