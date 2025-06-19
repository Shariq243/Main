import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import Calendar
import sqlite3
from contextlib import contextmanager
import bcrypt  # Added for password hashing
import logging # Added for logging

# Configure logging for the combined application
logging.basicConfig(filename='medical_app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Shared Database Manager Section ---
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

# --- Medical Application (Patient/Doctor) Class Section ---
class MedicalApp:
    def __init__(self, root, db_manager_instance):
        self.root = root
        self.root.title("Medical Appointment System")
        self.current_user = None
        self.user_role = None  # "patient" or "doctor"
        self.db = db_manager_instance
        self.main_menu()

    # --- UI Utility Methods Section ---
    def clear_window(self):
        """Clear all widgets from the root window"""
        for widget in self.root.winfo_children():
            widget.destroy()

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

    # --- Main Menu Section ---
    def main_menu(self):
        self.clear_window()
        tk.Label(self.root, text="Welcome to Medical Appointment System", 
                font=("Arial", 16)).pack(pady=20)
        
        self.create_button(self.root, "Login", self.login_screen)
        self.create_button(self.root, "Register as Patient", lambda: self.register_screen("patient"))
        self.create_button(self.root, "Register as Doctor", lambda: self.register_screen("doctor"))

    # --- Registration Section ---
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

    # --- Login Section ---
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

    # --- Patient Dashboard Section ---
    def dashboard(self):
        self.clear_window()
        tk.Label(self.root, text=f"Welcome, {self.current_user}", 
                font=("Arial", 14)).pack(pady=10)
        
        self.create_button(self.root, "Book Appointment", self.book_appointment)
        self.create_button(self.root, "View My Appointments", self.view_my_appointments)
        self.create_button(self.root, "Search by Doctor/Date", self.search_appointments)
        self.create_button(self.root, "Logout", self.main_menu)
        logging.info(f"Patient dashboard loaded for: {self.current_user}")

    # --- Book Appointment Section ---
    def book_appointment(self):
        self.clear_window()
        tk.Label(self.root, text="Book Appointment", font=("Arial", 14)).pack(pady=10)

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

        tk.Label(self.root, text="Select Date").pack()
        cal = Calendar(self.root, selectmode='day')
        cal.pack(pady=5)

        time_entry = self.create_form_field(self.root, "Time (e.g., 10:00 AM)")

        def save():
            doctor = doctor_combo.get().strip()
            date = cal.get_date()
            time = time_entry.get().strip()
            
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

    # --- View My Appointments Section (Patient) ---
    def view_my_appointments(self):
        self.clear_window()
        tk.Label(self.root, text="My Appointments", font=("Arial", 14)).pack(pady=10)
        
        tree = ttk.Treeview(self.root, columns=("ID", "Doctor", "Date", "Time"), show='headings')
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

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

        self.create_button(self.root, "Delete Appointment", 
                         lambda: self._delete_appointment(tree))
        self.create_button(self.root, "Reschedule Appointment", 
                         lambda: self._reschedule_appointment(tree))
        self.create_button(self.root, "Back", self.dashboard)

    # --- Delete Appointment Method (Patient) ---
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
            self.view_my_appointments() 
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete appointment: {str(e)}")
            logging.error(f"Error deleting appointment ID {appointment_id} by {self.current_user}: {e}")

    # --- Reschedule Appointment Method (Patient) ---
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
                self.view_my_appointments() 
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reschedule: {str(e)}")
                logging.error(f"Error rescheduling appointment ID {appointment_id} by {self.current_user}: {e}")

        self.create_button(top, "Update", update)
        self.create_button(top, "Cancel", top.destroy)

    # --- Search Appointments Section (Patient) ---
    def search_appointments(self):
        self.clear_window()
        tk.Label(self.root, text="Search Appointments", font=("Arial", 14)).pack(pady=10)
        
        search_entry = self.create_form_field(self.root, "Doctor Name or Date (e.g. 05/31/2025)")

        tree = ttk.Treeview(self.root, columns=("Doctor", "Date", "Time"), show='headings')
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=180)
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
                               WHERE (doctor LIKE ? OR date = ?) AND patient_username = ?''',
                             (f"%{value}%", value, self.current_user))
                    for row in c.fetchall():
                        tree.insert('', 'end', values=row)
                logging.info(f"Appointments searched by {self.current_user} for term: '{value}'")
            except Exception as e:
                messagebox.showerror("Error", f"Search failed: {str(e)}")
                logging.error(f"Error during appointment search by {self.current_user} for '{value}': {e}")

        self.create_button(self.root, "Search", search)
        self.create_button(self.root, "Back", self.dashboard)

    # --- Doctor Dashboard Section ---
    def doctor_dashboard(self):
        self.clear_window()
        tk.Label(self.root, text=f"Doctor Dashboard - Dr. {self.current_user}", 
                font=("Arial", 14)).pack(pady=10)

        tree = ttk.Treeview(self.root, columns=("ID", "Patient", "Date", "Time"), show='headings')
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=150)
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
                         lambda: self._delete_appointment_doctor_view(tree))
        self.create_button(self.root, "Logout", self.main_menu)

    # --- Delete Appointment Method (Doctor's View) ---
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

# --- Admin System Class Section ---
class AdminSystem:
    def __init__(self, root, db_manager_instance):
        self.root = root
        self.root.title("Admin Dashboard")
        self.db = db_manager_instance
        self.setup_ui()
        
    # --- UI Utility Methods (Admin) Section ---
    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    # --- Admin Main Interface Setup Section ---
    def setup_ui(self):
        """Set up the main admin interface"""
        self.clear_window()
        tk.Label(self.root, text="Admin Dashboard", font=("Arial", 16)).pack(pady=20)
        
        buttons = [
            ("Manage Patients", self.manage_patients),
            ("Manage Doctors", self.manage_doctors),
            ("Manage Appointments", self.manage_appointments),
            ("Exit", self.root.quit)
        ]
        
        for text, command in buttons:
            tk.Button(self.root, text=text, command=command, width=20).pack(pady=5)
        logging.info("Admin dashboard loaded.")
    
    # --- Manage Patients Section (Admin) ---
    def manage_patients(self):
        """Manage patient accounts"""
        self.clear_window()
        tk.Label(self.root, text="Manage Patients", font=("Arial", 14)).pack(pady=10)
        
        tree = ttk.Treeview(self.root, columns=("ID", "Username"), show="headings")
        tree.heading("ID", text="ID")
        tree.column("ID", width=50)
        tree.heading("Username", text="Username")
        tree.column("Username", width=200)
        tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.load_patients(tree)
        
        tk.Button(self.root, text="Delete Selected", 
                 command=lambda: self.delete_record(tree, "patients")).pack(pady=5)
        tk.Button(self.root, text="Back", command=self.setup_ui).pack(pady=5)
        logging.info("Manage Patients screen loaded.")
    
    # --- Load Patients Method (Admin) ---
    def load_patients(self, tree):
        """Load patient data into treeview"""
        tree.delete(*tree.get_children())
        try:
            with self.db.get_cursor() as c:
                c.execute("SELECT id, username FROM patients")
                for row in c.fetchall():
                    tree.insert("", "end", values=row)
            logging.info("Patient data loaded into treeview for admin.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load patient data: {str(e)}")
            logging.error(f"Admin error loading patient data: {e}")
    
    # --- Manage Doctors Section (Admin) ---
    def manage_doctors(self):
        """Manage doctor accounts"""
        self.clear_window()
        tk.Label(self.root, text="Manage Doctors", font=("Arial", 14)).pack(pady=10)
        
        tree = ttk.Treeview(self.root, columns=("ID", "Username"), show="headings")
        tree.heading("ID", text="ID")
        tree.column("ID", width=50)
        tree.heading("Username", text="Username")
        tree.column("Username", width=200)
        tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.load_doctors(tree)
        
        tk.Label(self.root, text="Add New Doctor:").pack()
        
        frame = tk.Frame(self.root)
        frame.pack(pady=5)
        
        tk.Label(frame, text="Username:").pack(side=tk.LEFT)
        username_entry = tk.Entry(frame)
        username_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame, text="Password:").pack(side=tk.LEFT)
        password_entry = tk.Entry(frame, show="*")
        password_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(self.root, text="Add Doctor", 
                 command=lambda: self.add_doctor(
                     username_entry.get(), 
                     password_entry.get(), 
                     tree
                 )).pack(pady=5)
        
        tk.Button(self.root, text="Delete Selected", 
                 command=lambda: self.delete_record(tree, "doctors")).pack(pady=5)
        tk.Button(self.root, text="Back", command=self.setup_ui).pack(pady=5)
        logging.info("Manage Doctors screen loaded.")
    
    # --- Load Doctors Method (Admin) ---
    def load_doctors(self, tree):
        """Load doctor data into treeview"""
        tree.delete(*tree.get_children())
        try:
            with self.db.get_cursor() as c:
                c.execute("SELECT id, username FROM doctors")
                for row in c.fetchall():
                    tree.insert("", "end", values=row)
            logging.info("Doctor data loaded into treeview for admin.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load doctor data: {str(e)}")
            logging.error(f"Admin error loading doctor data: {e}")
    
    # --- Manage Appointments Section (Admin) ---
    def manage_appointments(self):
        """Manage all appointments"""
        self.clear_window()
        tk.Label(self.root, text="Manage Appointments", font=("Arial", 14)).pack(pady=10)
        
        tree = ttk.Treeview(self.root, columns=("ID", "Patient", "Doctor", "Date", "Time"), show="headings")
        for col in ["ID", "Patient", "Doctor", "Date", "Time"]:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.load_appointments(tree)
        
        tk.Button(self.root, text="Delete Selected", 
                 command=lambda: self.delete_record(tree, "appointments")).pack(pady=5)
        tk.Button(self.root, text="Back", command=self.setup_ui).pack(pady=5)
        logging.info("Manage Appointments screen loaded.")
    
    # --- Load Appointments Method (Admin) ---
    def load_appointments(self, tree):
        """Load appointment data into treeview"""
        tree.delete(*tree.get_children())
        try:
            with self.db.get_cursor() as c:
                c.execute("SELECT id, patient_username, doctor, date, time FROM appointments")
                for row in c.fetchall():
                    tree.insert("", "end", values=row)
            logging.info("Appointment data loaded into treeview for admin.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load appointment data: {str(e)}")
            logging.error(f"Admin error loading appointment data: {e}")
    
    # --- Add Doctor Method (Admin) ---
    def add_doctor(self, username, password, tree):
        """Add a new doctor account"""
        username = username.strip()
        password = password.strip()

        if not username or not password:
            messagebox.showerror("Error", "Username and password are required.")
            logging.warning("Admin tried to add doctor with empty fields.")
            return
            
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            with self.db.get_cursor() as c:
                c.execute("INSERT INTO doctors (username, password) VALUES (?, ?)", 
                         (username, hashed_password))
            messagebox.showinfo("Success", "Doctor added successfully.")
            logging.info(f"Doctor '{username}' added by admin.")
            self.load_doctors(tree)  # Refresh the doctor list
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
            logging.warning(f"Admin tried to add existing doctor username: '{username}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add doctor: {str(e)}")
            logging.error(f"Error adding doctor '{username}': {e}")
    
    # --- Delete Record Method (Admin) ---
    def delete_record(self, tree, table):
        """Delete a selected record from the database"""
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", f"Please select a {table[:-1]} to delete.")
            logging.warning(f"Admin tried to delete from '{table}' without selection.")
            return
            
        record_id = tree.item(selected[0])['values'][0]
        
        try:
            with self.db.get_cursor() as c:
                c.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
            messagebox.showinfo("Success", "Record deleted successfully.")
            logging.info(f"Record ID {record_id} deleted from '{table}' by admin.")
            
            # Refresh the current view
            if table == "patients":
                self.load_patients(tree)
            elif table == "doctors":
                self.load_doctors(tree)
            else:
                self.load_appointments(tree)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete record: {str(e)}")
            logging.error(f"Error deleting record ID {record_id} from '{table}': {e}")


# --- Main Application Launcher Section ---
if __name__ == "__main__":
    # Initialize the DatabaseManager once for the entire application
    db_manager = DatabaseManager() 

    # Create a main root window for selecting the role
    main_launcher_root = tk.Tk()
    main_launcher_root.title("Medical Appointment System Launcher")
    main_launcher_root.geometry("400x300")
    main_launcher_root.resizable(False, False)

    tk.Label(main_launcher_root, text="Select Your Application Role", font=("Arial", 14)).pack(pady=30)

    # --- Launch Patient/Doctor App Function ---
    def launch_patient_doctor_app():
        main_launcher_root.destroy()
        app_root = tk.Tk()
        app_root.geometry("600x550")
        app_root.title("Medical Appointment System")
        MedicalApp(app_root, db_manager) # Pass the shared db_manager instance
        app_root.mainloop()

    # --- Launch Admin Login Process Function ---
    def launch_admin_login_process():
        main_launcher_root.destroy()
        
        admin_login_root = tk.Tk()
        admin_login_root.title("Admin Login")
        admin_login_root.geometry("300x200")
        admin_login_root.resizable(False, False)
        
        tk.Label(admin_login_root, text="Admin Login", font=("Arial", 14)).pack(pady=10)
        
        frame = tk.Frame(admin_login_root)
        frame.pack(pady=10)
        
        tk.Label(frame, text="Username:").grid(row=0, column=0, sticky="e")
        username_entry = tk.Entry(frame)
        username_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(frame, text="Password:").grid(row=1, column=0, sticky="e")
        password_entry = tk.Entry(frame, show="*")
        password_entry.grid(row=1, column=1, padx=5)
        
        ADMIN_USERNAME = "admin"
        # Hashed password for "admin123" - GENERATED ONCE AND STORED HERE
        # IMPORTANT: Replace the placeholder hash below with the actual hash generated
        # by running the bcrypt hash generation script on your system.
        ADMIN_PASSWORD_HASH = b'$2b$12$zHzY88X5SIJ3qAVLgNgldeETJC4MetiJg0qPs6jJt63/dOPc07Koi' 

        def perform_admin_login():
            entered_username = username_entry.get().strip()
            entered_password = password_entry.get().strip()

            if not entered_username or not entered_password:
                messagebox.showerror("Error", "Username and password cannot be empty.")
                logging.warning("Admin login attempt with empty fields.")
                return

            if entered_username == ADMIN_USERNAME and \
               bcrypt.checkpw(entered_password.encode('utf-8'), ADMIN_PASSWORD_HASH): # No .encode() on ADMIN_PASSWORD_HASH as it's already bytes
                admin_login_root.destroy()
                admin_root = tk.Tk()
                admin_root.geometry("800x600")
                admin_root.title("Admin Dashboard")
                AdminSystem(admin_root, db_manager) # Pass the shared db_manager instance
                admin_root.mainloop()
                logging.info(f"Admin '{entered_username}' successfully logged in.")
            else:
                messagebox.showerror("Error", "Invalid admin credentials.")
                logging.warning(f"Failed admin login attempt for username: '{entered_username}'.")
        
        tk.Button(admin_login_root, text="Login", command=perform_admin_login).pack(pady=10)
        admin_login_root.mainloop()

    # --- Main Launcher Buttons Section ---
    tk.Button(main_launcher_root, text="Patient / Doctor Application", command=launch_patient_doctor_app, width=30).pack(pady=10)
    tk.Button(main_launcher_root, text="Admin Panel Login", command=launch_admin_login_process, width=30).pack(pady=10)

    main_launcher_root.mainloop()
