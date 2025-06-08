# hello.py
import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import Calendar
import sqlite3
from contextlib import contextmanager
import bcrypt # Added for password hashing
import logging # Added for logging

# Configure logging
logging.basicConfig(filename='medical_app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# -------------------- Database Refactoring --------------------
class DatabaseManager:
    """Centralized database management with context manager"""
    def __init__(self, db_name="medical_appointments.db"):
        self.db_name = db_name
        self._create_tables()
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Database error: {e}")
            raise e
        finally:
            conn.close()
    
    def _create_tables(self):
        """Initialize database tables"""
        with self.get_cursor() as c:
            c.execute('''CREATE TABLE IF NOT EXISTS patients (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT)''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS doctors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT)''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_username TEXT,
                        doctor TEXT,
                        date TEXT,
                        time TEXT)''')

# -------------------- Application Classes --------------------
class MedicalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Medical Appointment System")
        self.current_user = None
        self.user_role = None  # "patient" or "doctor"
        self.db = DatabaseManager()  # Using the new DatabaseManager
        self.main_menu()

    def clear_window(self):
        """Clear all widgets from the root window"""
        for widget in self.root.winfo_children():
            widget.destroy()

    # -------------------- UI Component Refactoring --------------------
    def create_form_field(self, parent, label_text, show="", entry_var=None):
        """Helper method to create standardized form fields"""
        tk.Label(parent, text=label_text).pack()
        entry = tk.Entry(parent, show=show, textvariable=entry_var)
        entry.pack()
        return entry

    def create_button(self, parent, text, command, width=20, pady=5):
        """Helper method to create standardized buttons"""
        btn = tk.Button(parent, text=text, command=command, width=width)
        btn.pack(pady=pady)
        return btn

    def main_menu(self):
        self.clear_window()
        tk.Label(self.root, text="Welcome to Medical Appointment System", 
                font=("Arial", 16)).pack(pady=20)
        
        self.create_button(self.root, "Login", self.login_screen)
        self.create_button(self.root, "Register as Patient", lambda: self.register_screen("patient"))
        self.create_button(self.root, "Register as Doctor", lambda: self.register_screen("doctor"))

    # -------------------- Registration Refactoring --------------------
    def register_screen(self, role):
        self.clear_window()
        tk.Label(self.root, text=f"Register as {role.capitalize()}", 
                font=("Arial", 16)).pack(pady=10)
        
        username_entry = self.create_form_field(self.root, "Username")
        password_entry = self.create_form_field(self.root, "Password", show="*")

        def register():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            
            # Input Validation
            if not username or not password:
                messagebox.showerror("Error", "Username and password cannot be empty.")
                logging.warning(f"Registration attempt with empty fields for role: {role}")
                return

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            try:
                with self.db.get_cursor() as c:
                    table = "patients" if role == "patient" else "doctors"
                    c.execute(f"INSERT INTO {table} (username, password) VALUES (?, ?)", 
                             (username, hashed_password))
                messagebox.showinfo("Success", f"{role.capitalize()} registration successful!")
                logging.info(f"Successful registration for {role}: {username}")
                self.main_menu()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists")
                logging.warning(f"Registration failed: Username '{username}' already exists for role: {role}")
            except Exception as e:
                messagebox.showerror("Error", f"Registration failed: {str(e)}")
                logging.error(f"Registration error for {role}: {e}")

        self.create_button(self.root, "Register", register)
        self.create_button(self.root, "Back", self.main_menu)

    # -------------------- Login Refactoring --------------------
    def login_screen(self):
        self.clear_window()
        tk.Label(self.root, text="Login", font=("Arial", 16)).pack(pady=10)

        role_var = tk.StringVar(value="patient")
        tk.Label(self.root, text="Select Role").pack()
        ttk.Combobox(self.root, textvariable=role_var, 
                    values=["patient", "doctor"], state="readonly").pack()

        username_entry = self.create_form_field(self.root, "Username")
        password_entry = self.create_form_field(self.root, "Password", show="*")

        def login():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            role = role_var.get()

            # Input Validation
            if not username or not password:
                messagebox.showerror("Error", "Username and password cannot be empty.")
                logging.warning(f"Login attempt with empty fields for role: {role}")
                return

            try:
                with self.db.get_cursor() as c:
                    table = "patients" if role == "patient" else "doctors"
                    c.execute(f"SELECT password FROM {table} WHERE username = ?", (username,))
                    user_data = c.fetchone()

                    if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data[0].encode('utf-8')):
                        self.current_user = username
                        self.user_role = role
                        messagebox.showinfo("Success", f"Logged in as {username} ({role})")
                        logging.info(f"Successful login for {role}: {username}")
                        self.dashboard() if role == "patient" else self.doctor_dashboard()
                    else:
                        messagebox.showerror("Error", "Invalid credentials")
                        logging.warning(f"Failed login attempt for {role}: {username}")
            except Exception as e:
                messagebox.showerror("Error", f"Login failed: {str(e)}")
                logging.error(f"Login error for {role}: {e}")

        self.create_button(self.root, "Login", login)
        self.create_button(self.root, "Back", self.main_menu)

    # -------------------- Dashboard Refactoring --------------------
    def dashboard(self):
        self.clear_window()
        tk.Label(self.root, text=f"Welcome, {self.current_user}", 
                font=("Arial", 14)).pack(pady=10)
        
        self.create_button(self.root, "Book Appointment", self.book_appointment)
        self.create_button(self.root, "View My Appointments", self.view_my_appointments)
        self.create_button(self.root, "Search by Doctor/Date", self.search_appointments)
        self.create_button(self.root, "Logout", self.main_menu)
        logging.info(f"Patient dashboard loaded for: {self.current_user}")

    # -------------------- Appointment Booking Refactoring --------------------
    def book_appointment(self):
        self.clear_window()
        tk.Label(self.root, text="Book Appointment", font=("Arial", 14)).pack(pady=10)

        # Doctor selection
        tk.Label(self.root, text="Select Doctor").pack()
        doctor_combo = ttk.Combobox(self.root, state="readonly")
        try:
            with self.db.get_cursor() as c:
                c.execute("SELECT username FROM doctors")
                doctor_combo["values"] = [row[0] for row in c.fetchall()]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load doctors: {str(e)}")
            logging.error(f"Error loading doctors for appointment booking: {e}")
            self.dashboard()
            return
        doctor_combo.pack()

        # Date selection
        tk.Label(self.root, text="Select Date").pack()
        cal = Calendar(self.root, selectmode='day')
        cal.pack(pady=5)

        # Time entry
        time_entry = self.create_form_field(self.root, "Time (e.g., 10:00 AM)")

        def save():
            doctor = doctor_combo.get().strip()
            date = cal.get_date()
            time = time_entry.get().strip()
            
            # Input Validation
            if not all([doctor, date, time]):
                messagebox.showerror("Error", "All fields are required to book an appointment.")
                logging.warning(f"Attempt to book appointment with missing fields by {self.current_user}")
                return

            try:
                with self.db.get_cursor() as c:
                    c.execute('''INSERT INTO appointments 
                               (patient_username, doctor, date, time) 
                               VALUES (?, ?, ?, ?)''',
                             (self.current_user, doctor, date, time))
                messagebox.showinfo("Success", "Appointment booked successfully!")
                logging.info(f"Appointment booked by {self.current_user} with Dr. {doctor} on {date} at {time}")
                self.dashboard()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to book appointment: {str(e)}")
                logging.error(f"Error booking appointment for {self.current_user}: {e}")

        self.create_button(self.root, "Save Appointment", save)
        self.create_button(self.root, "Back", self.dashboard)

    # -------------------- View Appointments Refactoring --------------------
    def view_my_appointments(self):
        self.clear_window()
        tk.Label(self.root, text="My Appointments", font=("Arial", 14)).pack(pady=10)
        
        # Create treeview
        tree = ttk.Treeview(self.root, columns=("ID", "Doctor", "Date", "Time"), show='headings')
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=150) # Added width for better display
        tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Populate appointments
        try:
            with self.db.get_cursor() as c:
                c.execute('''SELECT id, doctor, date, time 
                            FROM appointments 
                            WHERE patient_username = ?''', (self.current_user,))
                for row in c.fetchall():
                    tree.insert('', 'end', values=row)
            logging.info(f"Viewing appointments for patient: {self.current_user}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load appointments: {str(e)}")
            logging.error(f"Error loading appointments for patient {self.current_user}: {e}")
            self.dashboard()
            return

        # Appointment management buttons
        self.create_button(self.root, "Delete Appointment", 
                         lambda: self._delete_appointment(tree))
        self.create_button(self.root, "Reschedule Appointment", 
                         lambda: self._reschedule_appointment(tree))
        self.create_button(self.root, "Back", self.dashboard)

    def _delete_appointment(self, tree):
        """Handle appointment deletion"""
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select an appointment to delete.")
            logging.warning(f"Delete appointment attempt without selection by {self.current_user}")
            return
            
        appointment_id = tree.item(selected[0])['values'][0]
        try:
            with self.db.get_cursor() as c:
                c.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
            messagebox.showinfo("Deleted", "Appointment deleted successfully.")
            logging.info(f"Appointment ID {appointment_id} deleted by {self.current_user}")
            self.view_my_appointments() # Refresh the view
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete appointment: {str(e)}")
            logging.error(f"Error deleting appointment ID {appointment_id} by {self.current_user}: {e}")

    def _reschedule_appointment(self, tree):
        """Handle appointment rescheduling"""
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select an appointment to reschedule.")
            logging.warning(f"Reschedule appointment attempt without selection by {self.current_user}")
            return
            
        appointment_id = tree.item(selected[0])['values'][0]
        top = tk.Toplevel(self.root)
        top.title("Reschedule Appointment")

        tk.Label(top, text="Select New Date").pack()
        cal = Calendar(top, selectmode='day')
        cal.pack(pady=5)

        new_time_entry = self.create_form_field(top, "New Time (e.g., 02:30 PM)")

        def update():
            new_date = cal.get_date()
            new_time = new_time_entry.get().strip()
            
            # Input Validation
            if not new_date or not new_time:
                messagebox.showerror("Error", "New date and time are required.")
                logging.warning(f"Attempt to reschedule appointment ID {appointment_id} with missing fields.")
                return

            try:
                with self.db.get_cursor() as c:
                    c.execute('''UPDATE appointments 
                               SET date = ?, time = ? 
                               WHERE id = ?''', 
                             (new_date, new_time, appointment_id))
                messagebox.showinfo("Success", "Appointment rescheduled successfully.")
                logging.info(f"Appointment ID {appointment_id} rescheduled by {self.current_user} to {new_date} at {new_time}")
                top.destroy()
                self.view_my_appointments() # Refresh the view
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reschedule: {str(e)}")
                logging.error(f"Error rescheduling appointment ID {appointment_id} by {self.current_user}: {e}")

        self.create_button(top, "Update", update)
        self.create_button(top, "Cancel", top.destroy) # Added cancel button

    # -------------------- Search Functionality --------------------
    def search_appointments(self):
        self.clear_window()
        tk.Label(self.root, text="Search Appointments", font=("Arial", 14)).pack(pady=10)
        
        search_entry = self.create_form_field(self.root, "Doctor Name or Date (e.g. 05/31/25)")

        tree = ttk.Treeview(self.root, columns=("Doctor", "Date", "Time"), show='headings')
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=180) # Adjusted width
        tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        def search():
            value = search_entry.get().strip()
            tree.delete(*tree.get_children())
            
            if not value:
                messagebox.showwarning("Warning", "Please enter a search term.")
                logging.warning(f"Search appointment attempt with empty search term by {self.current_user}")
                return

            try:
                with self.db.get_cursor() as c:
                    c.execute('''SELECT doctor, date, time 
                               FROM appointments 
                               WHERE (doctor LIKE ? OR date = ?) AND patient_username = ?''', # Added patient filter
                             (f"%{value}%", value, self.current_user))
                    for row in c.fetchall():
                        tree.insert('', 'end', values=row)
                logging.info(f"Appointments searched by {self.current_user} for term: '{value}'")
            except Exception as e:
                messagebox.showerror("Error", f"Search failed: {str(e)}")
                logging.error(f"Error during appointment search by {self.current_user} for '{value}': {e}")

        self.create_button(self.root, "Search", search)
        self.create_button(self.root, "Back", self.dashboard)

    # -------------------- Doctor Dashboard --------------------
    def doctor_dashboard(self):
        self.clear_window()
        tk.Label(self.root, text=f"Doctor Dashboard - Dr. {self.current_user}", 
                font=("Arial", 14)).pack(pady=10)

        tree = ttk.Treeview(self.root, columns=("ID", "Patient", "Date", "Time"), show='headings')
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=150) # Added width for better display
        tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        try:
            with self.db.get_cursor() as c:
                c.execute('''SELECT id, patient_username, date, time 
                            FROM appointments 
                            WHERE doctor = ?''', (self.current_user,))
                for row in c.fetchall():
                    tree.insert('', 'end', values=row)
            logging.info(f"Doctor dashboard loaded for: {self.current_user}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load appointments for doctor: {str(e)}")
            logging.error(f"Error loading appointments for doctor {self.current_user}: {e}")
            self.main_menu()
            return

        self.create_button(self.root, "Delete Appointment", 
                         lambda: self._delete_appointment_doctor_view(tree)) # Separate delete for doctor view
        self.create_button(self.root, "Logout", self.main_menu)

    def _delete_appointment_doctor_view(self, tree):
        """Handle appointment deletion from doctor's view"""
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select an appointment to delete.")
            logging.warning(f"Delete appointment attempt without selection by doctor {self.current_user}")
            return
            
        appointment_id = tree.item(selected[0])['values'][0]
        try:
            with self.db.get_cursor() as c:
                c.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
            messagebox.showinfo("Deleted", "Appointment deleted successfully.")
            logging.info(f"Appointment ID {appointment_id} deleted by doctor {self.current_user}")
            self.doctor_dashboard() # Refresh the view
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete appointment: {str(e)}")
            logging.error(f"Error deleting appointment ID {appointment_id} by doctor {self.current_user}: {e}")

# -------------------- Run Application --------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = MedicalApp(root)
    root.geometry("600x550")
    root.mainloop()