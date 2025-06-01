import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import Calendar
import sqlite3
from contextlib import contextmanager

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
        self.create_button(self.root, "Register as Patient", self.register_patient_screen)
        self.create_button(self.root, "Register as Doctor", self.register_doctor_screen)

    # -------------------- Registration Refactoring --------------------
    def register_screen(self, role):
        self.clear_window()
        tk.Label(self.root, text=f"Register as {role.capitalize()}", 
                font=("Arial", 16)).pack(pady=10)
        
        username_entry = self.create_form_field(self.root, "Username")
        password_entry = self.create_form_field(self.root, "Password", show="*")

        def register():
            username = username_entry.get()
            password = password_entry.get()
            
            try:
                with self.db.get_cursor() as c:
                    table = "patients" if role == "patient" else "doctors"
                    c.execute(f"INSERT INTO {table} (username, password) VALUES (?, ?)", 
                             (username, password))
                messagebox.showinfo("Success", f"{role.capitalize()} registration successful!")
                self.main_menu()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists")

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
            username = username_entry.get()
            password = password_entry.get()
            role = role_var.get()

            try:
                with self.db.get_cursor() as c:
                    table = "patients" if role == "patient" else "doctors"
                    c.execute(f"SELECT * FROM {table} WHERE username = ? AND password = ?", 
                             (username, password))
                    if c.fetchone():
                        self.current_user = username
                        self.user_role = role
                        self.dashboard() if role == "patient" else self.doctor_dashboard()
                    else:
                        messagebox.showerror("Error", "Invalid credentials")
            except Exception as e:
                messagebox.showerror("Error", f"Login failed: {str(e)}")

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

    # -------------------- Appointment Booking Refactoring --------------------
    def book_appointment(self):
        self.clear_window()
        tk.Label(self.root, text="Book Appointment", font=("Arial", 14)).pack(pady=10)

        # Doctor selection
        tk.Label(self.root, text="Select Doctor").pack()
        doctor_combo = ttk.Combobox(self.root, state="readonly")
        with self.db.get_cursor() as c:
            c.execute("SELECT username FROM doctors")
            doctor_combo["values"] = [row[0] for row in c.fetchall()]
        doctor_combo.pack()

        # Date selection
        tk.Label(self.root, text="Select Date").pack()
        cal = Calendar(self.root, selectmode='day')
        cal.pack(pady=5)

        # Time entry
        time_entry = self.create_form_field(self.root, "Time (e.g., 10:00 AM)")

        def save():
            doctor = doctor_combo.get()
            date = cal.get_date()
            time = time_entry.get()
            
            if not all([doctor, date, time]):
                messagebox.showerror("Error", "All fields required")
                return

            try:
                with self.db.get_cursor() as c:
                    c.execute('''INSERT INTO appointments 
                               (patient_username, doctor, date, time) 
                               VALUES (?, ?, ?, ?)''',
                             (self.current_user, doctor, date, time))
                messagebox.showinfo("Success", "Appointment booked successfully!")
                self.dashboard()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to book appointment: {str(e)}")

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
        tree.pack()

        # Populate appointments
        with self.db.get_cursor() as c:
            c.execute('''SELECT id, doctor, date, time 
                        FROM appointments 
                        WHERE patient_username = ?''', (self.current_user,))
            for row in c.fetchall():
                tree.insert('', 'end', values=row)

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
            return
            
        appointment_id = tree.item(selected[0])['values'][0]
        try:
            with self.db.get_cursor() as c:
                c.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
            messagebox.showinfo("Deleted", "Appointment deleted")
            self.view_my_appointments()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete appointment: {str(e)}")

    def _reschedule_appointment(self, tree):
        """Handle appointment rescheduling"""
        selected = tree.selection()
        if not selected:
            return
            
        appointment_id = tree.item(selected[0])['values'][0]
        top = tk.Toplevel(self.root)
        top.title("Reschedule Appointment")

        tk.Label(top, text="Select New Date").pack()
        cal = Calendar(top, selectmode='day')
        cal.pack(pady=5)

        new_time_entry = self.create_form_field(top, "New Time")

        def update():
            new_date = cal.get_date()
            new_time = new_time_entry.get()
            
            try:
                with self.db.get_cursor() as c:
                    c.execute('''UPDATE appointments 
                               SET date = ?, time = ? 
                               WHERE id = ?''', 
                             (new_date, new_time, appointment_id))
                messagebox.showinfo("Success", "Appointment rescheduled")
                top.destroy()
                self.view_my_appointments()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reschedule: {str(e)}")

        self.create_button(top, "Update", update)

    # -------------------- Search Functionality --------------------
    def search_appointments(self):
        self.clear_window()
        tk.Label(self.root, text="Search Appointments", font=("Arial", 14)).pack(pady=10)
        
        search_entry = self.create_form_field(self.root, "Doctor Name or Date (e.g. 05/31/25)")

        tree = ttk.Treeview(self.root, columns=("Doctor", "Date", "Time"), show='headings')
        for col in tree["columns"]:
            tree.heading(col, text=col)
        tree.pack()

        def search():
            value = search_entry.get()
            tree.delete(*tree.get_children())
            
            try:
                with self.db.get_cursor() as c:
                    c.execute('''SELECT doctor, date, time 
                               FROM appointments 
                               WHERE doctor LIKE ? OR date = ?''',
                             (f"%{value}%", value))
                    for row in c.fetchall():
                        tree.insert('', 'end', values=row)
            except Exception as e:
                messagebox.showerror("Error", f"Search failed: {str(e)}")

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
        tree.pack()

        with self.db.get_cursor() as c:
            c.execute('''SELECT id, patient_username, date, time 
                        FROM appointments 
                        WHERE doctor = ?''', (self.current_user,))
            for row in c.fetchall():
                tree.insert('', 'end', values=row)

        self.create_button(self.root, "Delete Appointment", 
                         lambda: self._delete_appointment(tree))
        self.create_button(self.root, "Logout", self.main_menu)

# -------------------- Run Application --------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = MedicalApp(root)
    root.geometry("600x550")
    root.mainloop()