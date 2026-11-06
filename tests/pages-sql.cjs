// Teste de isolamento das políticas com PostgreSQL local em memória (PGlite).
const fs=require('fs'),path=require('path');
const {PGlite}=require(process.env.PERICIA_NODE_MODULES?path.join(process.env.PERICIA_NODE_MODULES,'@electric-sql/pglite'):'@electric-sql/pglite');
(async()=>{
 const db=new PGlite();
 try{
 await db.exec(`
 create role anon; create role authenticated;
 create schema auth; create schema storage;
 create table auth.users(id uuid primary key);
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 create table storage.buckets(id text primary key,name text,public boolean,file_size_limit bigint);
 create table storage.objects(id integer generated always as identity,name text,bucket_id text);
 create function storage.foldername(text) returns text[] language sql immutable as $$select string_to_array($1,'/')$$;
 alter table storage.objects enable row level security;
 grant usage on schema public,auth,storage to anon,authenticated;
 grant select,insert,update,delete on storage.objects to authenticated;
 grant usage on all sequences in schema storage to authenticated;
 insert into auth.users values ('11111111-1111-4111-8111-111111111111'),('22222222-2222-4222-8222-222222222222');
 `);
 await db.exec(fs.readFileSync(path.join(__dirname,'../deploy/supabase.sql'),'utf8'));
 const state={case:'TEST',notes:'',tasks:[{id:1,status:'pendente',notes:''}],questions:[{id:1,answer:'',evidence:''}],activity:[]};
 await db.query('insert into pericia_cases(user_id,state) values ($1,$2)', ['11111111-1111-4111-8111-111111111111',JSON.stringify(state)]);
 await db.exec("set role authenticated; select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',false)");
 const result=await db.query("select pericia_update('tasks',1,'{\"status\":\"andamento\"}') as state");
 if(result.rows[0].state.tasks[0].status!=='andamento')throw Error('Update failed');
 await db.query("select pericia_update('questions',1,'{\"answer\":\"Test answer\"}')");
 await db.query("select pericia_update('notes',null,'{\"notes\":\"Saved note\"}')");
 let rejected=false;try{await db.query("select pericia_update('tasks',1,'{\"status\":\"invalid\"}')");}catch{rejected=true;}if(!rejected)throw Error('Invalid status accepted');
 await db.exec("insert into storage.objects(name,bucket_id) values ('11111111-1111-4111-8111-111111111111/private.pdf','pericia-private')");
 await db.exec("select set_config('request.jwt.claim.sub','22222222-2222-4222-8222-222222222222',false)");
 if((await db.query('select * from pericia_cases')).rows.length)throw Error('Other user case leaked');
 if((await db.query('select * from storage.objects')).rows.length)throw Error('Other user file leaked');
 rejected=false;try{await db.exec("insert into storage.objects(name,bucket_id) values ('11111111-1111-4111-8111-111111111111/foreign.pdf','pericia-private')");}catch{rejected=true;}if(!rejected)throw Error('Foreign upload accepted');
 await db.exec('reset role; set role anon');
 rejected=false;try{await db.query('select * from pericia_cases');}catch{rejected=true;}if(!rejected)throw Error('Anonymous access accepted');
 console.log('PASS: PostgreSQL transactions, task/question/notes writes, invalid status, user isolation, private files and anonymous denial.');
 }finally{await db.close()}
})().catch(error=>{console.error(error);process.exit(1)});
