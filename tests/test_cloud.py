import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile


class CloudTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        os.environ.update(DATA_DIR=cls.temp.name, APP_PASSWORD='test-password-only-12345', SECRET_KEY='test-session-secret-' * 3, COOKIE_SECURE='false')
        spec = importlib.util.spec_from_file_location('cloud_test_app', Path(__file__).resolve().parents[1] / 'app.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.module.app.config['TESTING'] = True
        cls.client = cls.module.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_private_workflow(self):
        c = self.client
        for route in ('/', '/files/secret.pdf', '/api/backup', '/app.js'):
            self.assertIn(c.get(route).status_code, (302, 401))
        self.assertEqual(c.get('/healthz').json, {'status': 'ok'})
        c.get('/login')
        with c.session_transaction() as s: csrf = s['csrf']
        self.assertEqual(c.post('/login', data={'password':'wrong','csrf':csrf}).status_code, 200)
        self.assertEqual(c.post('/login', data={'password':'test-password-only-12345','csrf':csrf}).status_code, 302)
        with c.session_transaction() as s: csrf = s['csrf']
        self.assertEqual(c.post('/admin/import').status_code, 403)
        state = dict(case='TEST', stages=[], tasks=[dict(id=1,status='pendente',notes='',owner='',due='')], questions=[], activity=[], notes='')
        package = io.BytesIO()
        with zipfile.ZipFile(package, 'w') as z:
            z.writestr('state.json', json.dumps(state))
            z.writestr('Pericia_5090332/00_Gestao_e_indice/inventario.json', json.dumps([dict(path='docs/test.pdf',textPath='docs/test.txt')]))
            z.writestr('Pericia_5090332/docs/test.pdf', b'%PDF-test')
            z.writestr('Pericia_5090332/docs/test.txt', 'private text')
        package.seek(0)
        self.assertEqual(c.post('/admin/import', data={'csrf':csrf,'package':(package,'package.zip')}).status_code, 302)
        self.assertEqual(c.get('/api/state').json['case'], 'TEST')
        response = c.get('/files/docs/test.pdf')
        self.assertEqual(response.data, b'%PDF-test')
        response.close()
        self.assertEqual(c.get('/files/../../../app.py').status_code, 403)
        self.assertEqual(c.post('/api/update', json={'kind':'notes','fields':{'notes':'saved'}}).status_code, 403)
        update = c.post('/api/update', headers={'X-CSRF-Token':csrf}, json={'kind':'notes','fields':{'notes':'saved'}})
        self.assertEqual(update.status_code, 200)
        self.assertEqual(c.get('/api/state').json['notes'], 'saved')
        with zipfile.ZipFile(io.BytesIO(c.get('/api/full-backup').data)) as z:
            self.assertEqual(json.loads(z.read('state.json'))['notes'], 'saved')
            self.assertIn('Pericia_5090332/docs/test.pdf', z.namelist())
        self.assertEqual(c.post('/admin/import', data={'csrf':csrf}).status_code, 409)
        self.assertEqual(c.post('/logout', headers={'X-CSRF-Token':csrf}).status_code, 302)
        self.assertEqual(c.get('/files/docs/test.pdf').status_code, 302)


if __name__ == '__main__':
    unittest.main()
