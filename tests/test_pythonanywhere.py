import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from werkzeug.security import check_password_hash

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pa_setup', PROJECT / 'deploy/pythonanywhere_setup.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class PythonAnywhereTest(unittest.TestCase):
    def test_configuration_preserves_existing_data_and_uses_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            password = 'test-password-private-12345'
            config_file = setup.configure(home, password)
            config = json.loads(config_file.read_text())
            self.assertNotIn(password, config_file.read_text())
            self.assertTrue(check_password_hash(config['APP_PASSWORD_HASH'], password))
            record = Path(config['DATA_DIR']) / 'preserve.txt'
            record.write_text('private data')
            setup.configure(home)
            updated = json.loads(config_file.read_text())
            self.assertEqual(config['SECRET_KEY'], updated['SECRET_KEY'])
            self.assertEqual(config['APP_PASSWORD_HASH'], updated['APP_PASSWORD_HASH'])
            self.assertEqual(record.read_text(), 'private data')
            setup.configure(home, 'new-test-password-67890')
            changed = json.loads(config_file.read_text())
            self.assertFalse(check_password_hash(changed['APP_PASSWORD_HASH'], password))
            self.assertTrue(check_password_hash(changed['APP_PASSWORD_HASH'], 'new-test-password-67890'))
            self.assertEqual(changed['SECRET_KEY'], config['SECRET_KEY'])

    def test_wsgi_loads_private_config_and_authenticates_over_https(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_file = setup.configure(Path(temporary), 'wsgi-test-password-12345')
            environment = os.environ.copy()
            environment['PERICIA_CONFIG'] = str(config_file)
            code = '''import runpy,sys
application=runpy.run_path(sys.argv[1])['application']
client=application.test_client()
assert client.get('/',base_url='https://test.local').status_code==302
client.get('/login',base_url='https://test.local')
with client.session_transaction(base_url='https://test.local') as session: csrf=session['csrf']
response=client.post('/login',base_url='https://test.local',data={'password':'wsgi-test-password-12345','csrf':csrf})
assert response.status_code==302
assert 'Secure' in response.headers['Set-Cookie']
assert client.get('/admin/import',base_url='https://test.local').status_code==200
print('WSGI login OK')
'''
            result = subprocess.run([sys.executable, '-c', code, str(PROJECT / 'deploy/pythonanywhere_wsgi.py')], env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
