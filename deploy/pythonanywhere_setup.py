"""Instalação no plano gratuito sem enviar credenciais ao repositório."""
import argparse
import getpass
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]


def store_config(path, config):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix('.tmp')
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as output:
        json.dump(config, output, indent=2)
    temporary.replace(path)
    path.chmod(0o600)


def configure(home, password=None):
    from werkzeug.security import generate_password_hash
    config_file = home / '.config/pericia/config.json'
    if config_file.exists():
        config = json.loads(config_file.read_text(encoding='utf-8'))
    else:
        if password is None:
            raise ValueError('Defina uma senha para a primeira instalação.')
        config = {'SECRET_KEY': secrets.token_urlsafe(48), 'DATA_DIR': str(home / 'pericia-private')}
    if password is not None:
        if len(password) < 16:
            raise ValueError('Use uma senha com pelo menos 16 caracteres.')
        config['APP_PASSWORD_HASH'] = generate_password_hash(password)
    config['PROJECT_DIR'] = str(PROJECT)
    Path(config['DATA_DIR']).mkdir(parents=True, exist_ok=True, mode=0o700)
    store_config(config_file, config)
    return config_file


def main():
    parser = argparse.ArgumentParser(description='Prepara a hospedagem gratuita no PythonAnywhere.')
    parser.add_argument('--change-password', action='store_true', help='Troca a senha sem apagar os documentos.')
    args = parser.parse_args()
    if sys.platform != 'linux' or not Path('/home').exists():
        raise SystemExit('Execute este instalador no console Bash do PythonAnywhere, não no Windows local.')
    home = Path.home()
    virtualenv = home / '.virtualenvs/pericia'
    python = virtualenv / 'bin/python'
    if not python.exists():
        subprocess.run([sys.executable, '-m', 'venv', str(virtualenv)], check=True)
    subprocess.run([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '--no-cache-dir', '-r', str(PROJECT / 'deploy/requirements-free.txt')], check=True)
    # O console inicial pode não estar no virtualenv; configure usando o Python dele.
    if Path(sys.prefix).resolve() != virtualenv.resolve():
        subprocess.run([str(python), str(Path(__file__).resolve()), *sys.argv[1:]], check=True)
        return
    config_file = home / '.config/pericia/config.json'
    password = None
    if not config_file.exists() or args.change_password:
        password = getpass.getpass('Crie a senha do sistema (mínimo 16 caracteres; não aparece na tela): ')
        confirmation = getpass.getpass('Repita a senha: ')
        if password != confirmation:
            raise SystemExit('Senhas diferentes. Execute novamente.')
    try:
        configure(home, password)
    except ValueError as error:
        raise SystemExit(str(error))
    print('\nPreparação concluída. Nenhuma senha foi enviada ao GitHub.')
    print('No painel Web: crie uma aplicação com Manual configuration e Python', f'{sys.version_info.major}.{sys.version_info.minor}')
    print('Virtualenv:', virtualenv)
    print('Substitua o conteúdo da configuração WSGI pelo arquivo:', PROJECT / 'deploy/pythonanywhere_wsgi.py')
    print('Remova mapeamentos de Static files: todos os arquivos devem passar pelo login Flask.')
    print('Ative Force HTTPS no painel Web e clique Reload. Depois entre e importe o ZIP privado.')


if __name__ == '__main__':
    main()
