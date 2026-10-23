from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import imgserve


class FileBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.dest = self.root / 'keep'
        self.outside = self.root / 'outside.png'
        self.outside.write_bytes(b'private')
        self.args = patch.object(imgserve.sys, 'argv', ['imgserve.py', str(self.source), str(self.dest)])
        self.args.start()
        self.addCleanup(self.args.stop)
        self.client = imgserve.app.test_client()
        self.client.get('/')
        with self.client.session_transaction() as session:
            self.token = session['csrf_token']

    def post(self, name, token=True):
        data = {'delete_img': name}
        if token:
            data['csrf_token'] = self.token
        return self.client.post('/', data=data)

    def test_cross_site_mutation_requires_session_token(self):
        f = self.source / 'x.png'
        f.write_bytes(b'image')
        self.assertEqual(self.post('x.png', token=False).status_code, 403)
        self.assertTrue(f.exists())

    def test_paths_and_globs_cannot_delete_other_files(self):
        f = self.source / 'x.png'
        f.write_bytes(b'image')
        self.assertEqual(self.post('../outside.png').status_code, 400)
        self.assertEqual(self.post('*.png').status_code, 200)
        self.assertTrue(self.outside.exists())
        self.assertTrue(f.exists())

    def test_symlinks_cannot_serve_or_mutate_outside_source(self):
        (self.source / 'secret.png').symlink_to(self.outside)
        self.assertEqual(self.client.get('/secret.png').status_code, 404)
        self.assertEqual(self.post('secret.png').status_code, 200)
        self.assertEqual(self.outside.read_bytes(), b'private')

    def test_normal_favorite_and_delete(self):
        (self.source / 'x.png').write_bytes(b'image')
        response = self.client.post('/', data={'fav_img': 'x.png', 'csrf_token': self.token})
        self.assertEqual(response.status_code, 200)
        self.assertEqual((self.dest / 'x.png').read_bytes(), b'image')
        (self.source / 'y.png').write_bytes(b'image')
        self.assertEqual(self.post('y.png').status_code, 200)
        self.assertFalse((self.source / 'y.png').exists())
