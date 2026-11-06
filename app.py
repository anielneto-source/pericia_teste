"""Versão online: login, armazenamento persistente e importação privada."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timedelta, timezone
import hmac
import io
import json
import os
import secrets
import shutil
import tempfile
import threading
import time
import zipfile

from flask import Flask, abort, jsonify, redirect, render_template_string, request, send_file, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('DATA_DIR', ROOT / 'private')).resolve()
DATA.mkdir(parents=True, exist_ok=True)
BASE = DATA / 'Pericia_5090332'
STATE = DATA / 'state.json'
PASSWORD = os.environ.get('APP_PASSWORD', '')
SECRET = os.environ.get('SECRET_KEY', '')
PASSWORD_HASH = os.environ.get('APP_PASSWORD_HASH', '')
if (not PASSWORD_HASH and len(PASSWORD) < 16) or len(SECRET) < 32:
    raise RuntimeError('Configure APP_PASSWORD com 16 caracteres ou mais (ou APP_PASSWORD_HASH) e SECRET_KEY com 32 ou mais.')
if not PASSWORD_HASH:
    PASSWORD_HASH = generate_password_hash(PASSWORD)
app = Flask(__name__, static_folder=None)
app.config.update(SECRET_KEY=SECRET, MAX_CONTENT_LENGTH=100 * 1024 * 1024,
                  SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                  SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE', 'true') == 'true',
                  PERMANENT_SESSION_LIFETIME=timedelta(hours=8))
LOCK = threading.RLock()
ATTEMPTS = []

PAGE = '''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ title }} · Perícia</title>
<style>body{font:16px Segoe UI,Arial;background:#edf2e9;color:#234536;max-width:600px;margin:8vh auto;padding:24px}main{padding:32px;border:1px solid #d7e0d1;background:white;border-radius:12px}h1{font:30px Georgia}p{line-height:1.7}input,button{font:inherit;padding:13px;border-radius:6px;box-sizing:border-box;width:100%;margin:10px 0;border:1px solid #cbd8c3}button{background:#244f3e;color:white;cursor:pointer}a{color:#345f40}.error{color:#a43b2d}</style><main><h1>{{ title }}</h1>{{ body|safe }}</main></html>'''

@app.before_request
def protect():
    session.setdefault('csrf', secrets.token_urlsafe(32))
    if request.path == '/healthz':
        return None
    if request.method == 'POST':
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf', '')
        if not hmac.compare_digest(str(token), session['csrf']):
            abort(403)
    if request.path == '/login':
        return None
    if not session.get('authenticated'):
        if request.path.startswith('/api/'):
            return jsonify(error='Sessão expirada. Entre novamente no sistema.'), 401
        return redirect('/login')
    if not STATE.exists() and request.path not in ('/admin/import', '/logout'):
        return redirect('/admin/import')

@app.after_request
def headers(response):
    response.headers.update({'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
                             'Referrer-Policy': 'same-origin', 'X-Frame-Options': 'DENY',
                             'Content-Security-Policy': "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; object-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'self'"})
    return response

@app.get('/healthz')
def health():
    return jsonify(status='ok')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        now = time.monotonic()
        with LOCK:
            ATTEMPTS[:] = [t for t in ATTEMPTS if now - t < 300]
            if len(ATTEMPTS) >= 15:
                return render_template_string(PAGE, title='Aguarde para tentar novamente', body='<p>Muitas tentativas. Tente novamente em cinco minutos.</p>'), 429
            ATTEMPTS.append(now)
        if check_password_hash(PASSWORD_HASH, request.form.get('password', '')):
            session.clear()
            session.update(authenticated=True, csrf=secrets.token_urlsafe(32))
            session.permanent = True
            return redirect('/')
        error = 'Senha incorreta.'
    body = '<p>Acesso privado aos documentos e ao acompanhamento da perícia.</p>'
    body += '<p class="error">' + error + '</p>'
    body += '<form method="post"><input type="hidden" name="csrf" value="' + session['csrf'] + '"><label for="password">Senha de acesso</label><input id="password" name="password" type="password" autocomplete="current-password" required><button>Entrar</button></form>'
    return render_template_string(PAGE, title='Entrar no sistema', body=body)

@app.post('/logout')
def logout():
    session.clear()
    return redirect('/login')

def read_state():
    return json.loads(STATE.read_text(encoding='utf-8'))

@app.get('/api/session')
def get_session():
    return jsonify(csrf=session['csrf'])

@app.get('/api/state')
def get_state():
    with LOCK:
        return jsonify(read_state())

@app.get('/api/documents')
def get_documents():
    with LOCK:
        return send_file(BASE / '00_Gestao_e_indice' / 'inventario.json', mimetype='application/json')

@app.get('/api/tree')
def get_tree():
    with LOCK:
        return jsonify([dict(path=p.relative_to(BASE).as_posix(), name=p.name, directory=p.is_dir(), size=p.stat().st_size if p.is_file() else 0) for p in sorted(BASE.rglob('*'))])

@app.get('/api/backup')
def backup():
    with LOCK:
        return send_file(io.BytesIO(STATE.read_bytes()), mimetype='application/json', as_attachment=True, download_name='plano-pericia-backup.json')

@app.get('/api/full-backup')
def full_backup():
    output = io.BytesIO()
    with LOCK, zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(STATE, 'state.json')
        for p in BASE.rglob('*'):
            if p.is_file():
                archive.write(p, p.relative_to(DATA).as_posix())
    output.seek(0)
    return send_file(output, mimetype='application/zip', as_attachment=True, download_name='pericia-backup-completo.zip')

@app.post('/api/update')
def update():
    try:
        update = request.get_json()
        kind, fields = update['kind'], update['fields']
        if kind not in ('tasks', 'questions', 'notes') or not isinstance(fields, dict) or not all(isinstance(v, str) for v in fields.values()):
            raise ValueError()
        with LOCK:
            state = read_state()
            if kind == 'notes':
                if set(fields) != {'notes'}: raise ValueError()
                state['notes'] = fields['notes']
            else:
                item = next(x for x in state[kind] if x['id'] == update['id'])
                allowed = {'status', 'due', 'notes', 'owner'} if kind == 'tasks' else {'answer', 'evidence'}
                if not set(fields) <= allowed: raise ValueError()
                if 'status' in fields and fields['status'] not in ('pendente', 'andamento', 'concluida', 'bloqueada'): raise ValueError()
                if fields.get('due'): datetime.strptime(fields['due'], '%Y-%m-%d')
                item.update(fields)
            state['activity'].insert(0, dict(time=datetime.now(timezone.utc).isoformat(), text='Anotações gerais atualizadas' if kind == 'notes' else f"{'Tarefa' if kind == 'tasks' else 'Quesito'} {update['id']} atualizado"))
            state['activity'] = state['activity'][:200]
            shutil.copy2(STATE, STATE.with_suffix('.previous.json'))
            temp = STATE.with_suffix('.tmp')
            temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
            temp.replace(STATE)
        return jsonify(state)
    except (ValueError, KeyError, TypeError, StopIteration):
        return jsonify(error='Dados inválidos'), 400

def validate_package(folder):
    state = json.loads((folder / 'state.json').read_text(encoding='utf-8'))
    for key in ('tasks', 'questions', 'stages', 'activity'):
        if not isinstance(state[key], list): raise ValueError('Estrutura do acompanhamento inválida.')
    for key in ('case', 'notes'):
        if not isinstance(state[key], str): raise ValueError('Estrutura do acompanhamento inválida.')
    root = folder / 'Pericia_5090332'
    catalog = json.loads((root / '00_Gestao_e_indice' / 'inventario.json').read_text(encoding='utf-8'))
    for doc in catalog:
        for key in ('path', 'textPath'):
            p = (root / doc[key]).resolve()
            if not p.is_relative_to(root.resolve()) or not p.is_file(): raise ValueError('Arquivo ausente no pacote.')

@app.route('/admin/import', methods=['GET', 'POST'])
def import_package():
    message = ''
    if request.method == 'POST':
        if STATE.exists(): abort(409, 'A importação inicial já foi realizada. Os dados existentes foram preservados.')
        upload = request.files.get('package')
        if not upload: abort(400)
        try:
            with tempfile.TemporaryDirectory(dir=DATA) as temporary:
                folder = Path(temporary)
                with zipfile.ZipFile(upload.stream) as archive:
                    entries = archive.infolist()
                    if len(entries) > 10000 or sum(e.file_size for e in entries) > 300 * 1024 * 1024:
                        raise ValueError('Pacote muito grande.')
                    for entry in entries:
                        name = PurePosixPath(entry.filename)
                        if name.is_absolute() or '..' in name.parts or '\\' in entry.filename or ':' in entry.filename:
                            raise ValueError('Caminho inválido.')
                        if entry.filename != 'state.json' and (not name.parts or name.parts[0] != 'Pericia_5090332'):
                            raise ValueError('Conteúdo fora da estrutura esperada.')
                        if entry.is_dir():
                            (folder / entry.filename).mkdir(parents=True, exist_ok=True)
                        else:
                            target = folder / entry.filename
                            target.parent.mkdir(parents=True, exist_ok=True)
                            with archive.open(entry) as source, target.open('wb') as dest:
                                shutil.copyfileobj(source, dest)
                validate_package(folder)
                with LOCK:
                    if STATE.exists(): abort(409)
                    if BASE.exists(): raise ValueError('Pasta de documentos já existente; confira o armazenamento antes de importar.')
                    shutil.move(str(folder / 'Pericia_5090332'), BASE)
                    shutil.move(str(folder / 'state.json'), STATE)
            return redirect('/')
        except (ValueError, KeyError, OSError, zipfile.BadZipFile, TypeError):
            message = '<p class="error">Pacote inválido ou incompatível. Envie o ZIP gerado pelo exportador local.</p>'
    body = '<p>Importe o pacote privado gerado no seu computador. O ZIP contém os PDFs, o índice e o acompanhamento. Ele será salvo no armazenamento privado do servidor.</p>'
    if STATE.exists():
        body += '<p>A importação inicial já foi concluída.</p><p><a href="/">Voltar ao sistema</a> · <a href="/api/full-backup">Baixar backup completo</a></p>'
    else:
        body += message + '<form method="post" enctype="multipart/form-data"><input type="hidden" name="csrf" value="' + session['csrf'] + '"><label>Pacote ZIP privado<input name="package" type="file" accept=".zip" required></label><button>Importar documentos e acompanhamento</button></form>'
    return render_template_string(PAGE, title='Documentos privados', body=body)

@app.get('/files/<path:filename>')
def files(filename):
    if Path(filename).suffix.lower() in ('.html', '.htm', '.svg', '.js', '.exe', '.bat', '.cmd', '.ps1', '.py'):
        abort(403)
    return send_from_directory(BASE, filename)

@app.get('/')
def index():
    return send_from_directory(ROOT / 'public', 'index.html')

@app.get('/<path:filename>')
def static_files(filename):
    return send_from_directory(ROOT / 'public', filename)
