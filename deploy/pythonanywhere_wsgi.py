"""Copie este arquivo para a configuração WSGI da aplicação no painel Web."""
import json
import os
from pathlib import Path
import sys

config_file = Path(os.environ.get('PERICIA_CONFIG', Path.home() / '.config/pericia/config.json'))
config = json.loads(config_file.read_text(encoding='utf-8'))
sys.path.insert(0, config['PROJECT_DIR'])
for name in ('APP_PASSWORD_HASH', 'SECRET_KEY', 'DATA_DIR'):
    os.environ[name] = config[name]
os.environ['COOKIE_SECURE'] = 'true'

from app import app as application
