
import unittest
import os
import sqlite3
from hello import DatabaseManager  # Assuming your main file is named main.py

TEST_DB = "test_medical_appointments.db"

class TestMedicalApp(unittest.TestCase):

    def setUp(self):
        """Set up a fresh test database before each test."""
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        self.db = DatabaseManager(TEST_DB)

    def test_patient_registration(self):
        with self.db.get_cursor() as c:
            c.execute("INSERT INTO patients (username, password) VALUES (?, ?)", ("test_user", "test_pass"))
            c.execute("SELECT * FROM patients WHERE username = ?", ("test_user",))
            user = c.fetchone()
        self.assertIsNotNone(user)
        self.assertEqual(user[1], "test_user")

    def test_doctor_registration(self):
        with self.db.get_cursor() as c:
            c.execute("INSERT INTO doctors (username, password) VALUES (?, ?)", ("doc_user", "doc_pass"))
            c.execute("SELECT * FROM doctors WHERE username = ?", ("doc_user",))
            user = c.fetchone()
        self.assertIsNotNone(user)
        self.assertEqual(user[1], "doc_user")

    def test_login_success(self):
        with self.db.get_cursor() as c:
            c.execute("INSERT INTO patients (username, password) VALUES (?, ?)", ("login_user", "1234"))
            c.execute("SELECT * FROM patients WHERE username = ? AND password = ?", ("login_user", "1234"))
            user = c.fetchone()
        self.assertIsNotNone(user)

    def test_book_appointment(self):
        with self.db.get_cursor() as c:
            c.execute("INSERT INTO doctors (username, password) VALUES (?, ?)", ("doc", "123"))
            c.execute("INSERT INTO patients (username, password) VALUES (?, ?)", ("pat", "123"))
            c.execute("INSERT INTO appointments (patient_username, doctor, date, time) VALUES (?, ?, ?, ?)",
                      ("pat", "doc", "06/01/25", "10:00 AM"))
            c.execute("SELECT * FROM appointments WHERE patient_username = ?", ("pat",))
            appointment = c.fetchone()
        self.assertIsNotNone(appointment)
        self.assertEqual(appointment[1], "pat")

    def test_reschedule_appointment(self):
        with self.db.get_cursor() as c:
            c.execute("INSERT INTO appointments (patient_username, doctor, date, time) VALUES (?, ?, ?, ?)",
                      ("pat", "doc", "06/01/25", "10:00 AM"))
            c.execute("UPDATE appointments SET date = ?, time = ? WHERE patient_username = ?",
                      ("06/02/25", "11:00 AM", "pat"))
            c.execute("SELECT date, time FROM appointments WHERE patient_username = ?", ("pat",))
            updated = c.fetchone()
        self.assertEqual(updated, ("06/02/25", "11:00 AM"))

    def test_delete_appointment(self):
        with self.db.get_cursor() as c:
            c.execute("INSERT INTO appointments (patient_username, doctor, date, time) VALUES (?, ?, ?, ?)",
                      ("pat", "doc", "06/01/25", "10:00 AM"))
            c.execute("DELETE FROM appointments WHERE patient_username = ?", ("pat",))
            c.execute("SELECT * FROM appointments WHERE patient_username = ?", ("pat",))
            result = c.fetchone()
        self.assertIsNone(result)

    def tearDown(self):
        """Remove test database after each test."""
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

if __name__ == "__main__":
    unittest.main()
