# admin.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import bcrypt # Added for password hashing
import logging # Added for logging
from hello import DatabaseManager # Assuming hello.py and admin.py will be merged or hello.py is accessible

# Configure logging for admin actions
logging.basicConfig(filename='admin_app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class AdminSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Dashboard")
        self.db = DatabaseManager() # Using the DatabaseManager from hello.py
        self.setup_ui()
        
    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def setup_ui(self):
        """Set up the main admin interface"""
        self.clear_window()
        tk.Label(self.root, text="Admin Dashboard", font=("Arial", 16)).pack(pady=20)
        
        # Main menu buttons
        buttons = [
            ("Manage Patients", self.manage_patients),
            ("Manage Doctors", self.manage_doctors),
            ("Manage Appointments", self.manage_appointments),
            ("Exit", self.root.quit)
        ]
        
        for text, command in buttons:
            tk.Button(self.root, text=text, command=command, width=20).pack(pady=5)
        logging.info("Admin dashboard loaded.")
    
    def manage_patients(self):
        """Manage patient accounts"""
        self.clear_window()
        tk.Label(self.root, text="Manage Patients", font=("Arial", 14)).pack(pady=10)
        
        # Treeview to display patients
        tree = ttk.Treeview(self.root, columns=("ID", "Username"), show="headings")
        tree.heading("ID", text="ID")
        tree.column("ID", width=50)
        tree.heading("Username", text="Username")
        tree.column("Username", width=200)
        tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Load patient data
        self.load_patients(tree)
        
        # Control buttons
        tk.Button(self.root, text="Delete Selected", 
                 command=lambda: self.delete_record(tree, "patients")).pack(pady=5)
        tk.Button(self.root, text="Back", command=self.setup_ui).pack(pady=5)
        logging.info("Manage Patients screen loaded.")
    
    def load_patients(self, tree):
        """Load patient data into treeview"""
        tree.delete(*tree.get_children())
        try:
            with self.db.get_cursor() as c:
                c.execute("SELECT id, username FROM patients")
                for row in c.fetchall():
                    tree.insert("", "end", values=row)
            logging.info("Patient data loaded into treeview.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load patient data: {str(e)}")
            logging.error(f"Error loading patient data: {e}")
    
    def manage_doctors(self):
        """Manage doctor accounts"""
        self.clear_window()
        tk.Label(self.root, text="Manage Doctors", font=("Arial", 14)).pack(pady=10)
        
        # Treeview to display doctors
        tree = ttk.Treeview(self.root, columns=("ID", "Username"), show="headings")
        tree.heading("ID", text="ID")
        tree.column("ID", width=50)
        tree.heading("Username", text="Username")
        tree.column("Username", width=200)
        tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Load doctor data
        self.load_doctors(tree)
        
        # Add doctor form
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
    
    def load_doctors(self, tree):
        """Load doctor data into treeview"""
        tree.delete(*tree.get_children())
        try:
            with self.db.get_cursor() as c:
                c.execute("SELECT id, username FROM doctors")
                for row in c.fetchall():
                    tree.insert("", "end", values=row)
            logging.info("Doctor data loaded into treeview.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load doctor data: {str(e)}")
            logging.error(f"Error loading doctor data: {e}")
    
    def manage_appointments(self):
        """Manage all appointments"""
        self.clear_window()
        tk.Label(self.root, text="Manage Appointments", font=("Arial", 14)).pack(pady=10)
        
        # Treeview to display appointments
        tree = ttk.Treeview(self.root, columns=("ID", "Patient", "Doctor", "Date", "Time"), show="headings")
        for col in ["ID", "Patient", "Doctor", "Date", "Time"]:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Load appointment data
        self.load_appointments(tree)
        
        # Control buttons
        tk.Button(self.root, text="Delete Selected", 
                 command=lambda: self.delete_record(tree, "appointments")).pack(pady=5)
        tk.Button(self.root, text="Back", command=self.setup_ui).pack(pady=5)
        logging.info("Manage Appointments screen loaded.")
    
    def load_appointments(self, tree):
        """Load appointment data into treeview"""
        tree.delete(*tree.get_children())
        try:
            with self.db.get_cursor() as c:
                c.execute("SELECT id, patient_username, doctor, date, time FROM appointments")
                for row in c.fetchall():
                    tree.insert("", "end", values=row)
            logging.info("Appointment data loaded into treeview.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load appointment data: {str(e)}")
            logging.error(f"Error loading appointment data: {e}")
    
    def add_doctor(self, username, password, tree):
        """Add a new doctor account"""
        username = username.strip()
        password = password.strip()

        # Input Validation
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
            messagebox.showerror("Error", "Username already exists.")
            logging.warning(f"Admin tried to add existing doctor username: '{username}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add doctor: {str(e)}")
            logging.error(f"Error adding doctor '{username}': {e}")
    
    def delete_record(self, tree, table):
        """Delete a selected record from the database"""
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", f"Please select a {table[:-1]} to delete.") # e.g., 'patient' from 'patients'
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

def admin_login():
    """Create a simple admin login window"""
    root = tk.Tk()
    root.title("Admin Login")
    root.geometry("300x200")
    
    tk.Label(root, text="Admin Login", font=("Arial", 14)).pack(pady=10)
    
    frame = tk.Frame(root)
    frame.pack(pady=10)
    
    tk.Label(frame, text="Username:").grid(row=0, column=0, sticky="e")
    username_entry = tk.Entry(frame)
    username_entry.grid(row=0, column=1, padx=5)
    
    tk.Label(frame, text="Password:").grid(row=1, column=0, sticky="e")
    password_entry = tk.Entry(frame, show="*")
    password_entry.grid(row=1, column=1, padx=5)
    
    # Hardcoded admin credentials (for demonstration, consider moving to config or environment variable)
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD_HASH = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def login():
        entered_username = username_entry.get().strip()
        entered_password = password_entry.get().strip()

        # Input Validation
        if not entered_username or not entered_password:
            messagebox.showerror("Error", "Username and password cannot be empty.")
            logging.warning("Admin login attempt with empty fields.")
            return

        # Verify admin credentials
        if entered_username == ADMIN_USERNAME and \
           bcrypt.checkpw(entered_password.encode('utf-8'), ADMIN_PASSWORD_HASH.encode('utf-8')):
            root.destroy()
            admin_root = tk.Tk()
            admin_root.geometry("800x600")
            AdminSystem(admin_root)
            admin_root.mainloop()
            logging.info(f"Admin '{entered_username}' successfully logged in.")
        else:
            messagebox.showerror("Error", "Invalid admin credentials.")
            logging.warning(f"Failed admin login attempt for username: '{entered_username}'.")
    
    tk.Button(root, text="Login", command=login).pack(pady=10)
    root.mainloop()

if __name__ == "__main__":
    # Ensure the DatabaseManager is initialized before admin_login to create tables if they don't exist
    # This might be redundant if hello.py's __main__ runs first, but good for standalone testing.
    DatabaseManager() 
    admin_login()