# test.py
import unittest
import os
import sqlite3
import bcrypt # Added for password hashing
from hello import DatabaseManager  # Assuming your main file is named hello.py

TEST_DB = "test_medical_appointments.db"

class TestMedicalApp(unittest.TestCase):

    def setUp(self):
        """Set up a fresh test database before each test."""
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        self.db = DatabaseManager(TEST_DB)

    def test_patient_registration(self):
        username = "test_user"
        password = "test_pass"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        with self.db.get_cursor() as c:
            c.execute("INSERT INTO patients (username, password) VALUES (?, ?)", (username, hashed_password))
            c.execute("SELECT * FROM patients WHERE username = ?", (username,))
            user = c.fetchone()
        self.assertIsNotNone(user)
        self.assertEqual(user[1], username)
        self.assertTrue(bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')))

    def test_doctor_registration(self):
        username = "doc_user"
        password = "doc_pass"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        with self.db.get_cursor() as c:
            c.execute("INSERT INTO doctors (username, password) VALUES (?, ?)", (username, hashed_password))
            c.execute("SELECT * FROM doctors WHERE username = ?", (username,))
            user = c.fetchone()
        self.assertIsNotNone(user)
        self.assertEqual(user[1], username)
        self.assertTrue(bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')))

    def test_login_success(self):
        username = "login_user"
        password = "123"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        with self.db.get_cursor() as c:
            c.execute("INSERT INTO patients (username, password) VALUES (?, ?)", (username, hashed_password))
            c.execute("SELECT password FROM patients WHERE username = ?", (username,))
            stored_hash = c.fetchone()[0]
        
        self.assertTrue(bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')))

    def test_login_failure(self):
        username = "fail_user"
        password = "wrong_pass"
        correct_password = "correct_pass"
        hashed_password = bcrypt.hashpw(correct_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        with self.db.get_cursor() as c:
            c.execute("INSERT INTO patients (username, password) VALUES (?, ?)", (username, hashed_password))
            c.execute("SELECT password FROM patients WHERE username = ?", (username,))
            stored_hash = c.fetchone()[0]
        
        self.assertFalse(bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')))

    def test_book_appointment(self):
        with self.db.get_cursor() as c:
            c.execute("INSERT INTO doctors (username, password) VALUES (?, ?)", ("doc", "123"))
            c.execute("INSERT INTO patients (username, password) VALUES (?, ?)", ("pat", "123"))
            c.execute("INSERT INTO appointments (patient_username, doctor, date, time) VALUES (?, ?, ?, ?)",
                      ("pat", "doc", "06/01/2025", "10:00 AM")) # Changed date format to match tkcalendar
            c.execute("SELECT * FROM appointments WHERE patient_username = ?", ("pat",))
            appointment = c.fetchone()
        self.assertIsNotNone(appointment)
        self.assertEqual(appointment[1], "pat")
        self.assertEqual(appointment[3], "06/01/2025")


    def test_reschedule_appointment(self):
        with self.db.get_cursor() as c:
            c.execute("INSERT INTO appointments (patient_username, doctor, date, time) VALUES (?, ?, ?, ?)",
                      ("pat_reschedule", "doc_reschedule", "06/01/2025", "10:00 AM"))
            c.execute("SELECT id FROM appointments WHERE patient_username = ?", ("pat_reschedule",))
            appointment_id = c.fetchone()[0]

            c.execute("UPDATE appointments SET date = ?, time = ? WHERE id = ?",
                      ("06/02/2025", "11:00 AM", appointment_id))
            c.execute("SELECT date, time FROM appointments WHERE id = ?", (appointment_id,))
            updated = c.fetchone()
        self.assertEqual(updated, ("06/02/2025", "11:00 AM"))

    def test_delete_appointment(self):
        with self.db.get_cursor() as c:
            c.execute("INSERT INTO appointments (patient_username, doctor, date, time) VALUES (?, ?, ?, ?)",
                      ("pat_delete", "doc_delete", "06/01/2025", "10:00 AM"))
            c.execute("SELECT id FROM appointments WHERE patient_username = ?", ("pat_delete",))
            appointment_id = c.fetchone()[0]

            c.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
            c.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
            result = c.fetchone()
        self.assertIsNone(result)

    def tearDown(self):
        """Remove test database after each test."""
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

if __name__ == "__main__":
    unittest.main()