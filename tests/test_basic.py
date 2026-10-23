import os, tempfile, unittest
from backend.app import app
from backend.database import db as database

class SmartProcureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        database.DB_PATH = __import__("pathlib").Path(self.tmp.name)
        database.init_db()
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret"
        self.client = app.test_client()
    def tearDown(self):
        try: os.unlink(self.tmp.name)
        except OSError: pass
    def test_empty_search_rejected(self):
        r = self.client.post("/api/search", json={})
        self.assertEqual(r.status_code, 400)
    def test_registration_and_duplicate(self):
        data = {"name":"Test User","email":"test@example.com","password":"password123","account_type":"individual"}
        self.assertEqual(self.client.post("/api/register",json=data).status_code,201)
        self.assertEqual(self.client.post("/api/register",json=data).status_code,409)
    def test_login_and_owner_history_endpoint(self):
        data = {"name":"Test User","email":"test@example.com","password":"password123","account_type":"individual"}
        self.client.post("/api/register",json=data)
        self.assertEqual(self.client.get("/api/history").status_code,200)
        self.client.post("/api/logout")
        self.assertEqual(self.client.get("/api/history").status_code,401)
if __name__ == "__main__": unittest.main()
