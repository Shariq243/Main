import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import Calendar
import sqlite3

# -------------------- Database Setup --------------------
conn = sqlite3.connect("medical_appointments.db")
c = conn.cursor()

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

conn.commit()

# -------------------- Application Classes --------------------
class MedicalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Medical Appointment System")
        self.current_user = None
        self.user_role = None  # "patient" or "doctor"
        self.main_menu()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def main_menu(self):
        self.clear_window()
        tk.Label(self.root, text="Welcome to Medical Appointment System", font=("Arial", 16)).pack(pady=20)
        tk.Button(self.root, text="Login", command=self.login_screen, width=20).pack(pady=10)
        tk.Button(self.root, text="Register as Patient", command=self.register_patient_screen, width=20).pack(pady=10)
        tk.Button(self.root, text="Register as Doctor", command=self.register_doctor_screen, width=20).pack(pady=10)

    def register_patient_screen(self):
        self.register_screen("patient")

    def register_doctor_screen(self):
        self.register_screen("doctor")

    def register_screen(self, role):
        self.clear_window()
        tk.Label(self.root, text=f"Register as {role.capitalize()}", font=("Arial", 16)).pack(pady=10)
        tk.Label(self.root, text="Username").pack()
        username_entry = tk.Entry(self.root)
        username_entry.pack()
        tk.Label(self.root, text="Password").pack()
        password_entry = tk.Entry(self.root, show="*")
        password_entry.pack()

        def register():
            username = username_entry.get()
            password = password_entry.get()
            try:
                if role == "patient":
                    c.execute("INSERT INTO patients (username, password) VALUES (?, ?)", (username, password))
                else:
                    c.execute("INSERT INTO doctors (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                messagebox.showinfo("Success", f"{role.capitalize()} registration successful!")
                self.main_menu()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists")

        tk.Button(self.root, text="Register", command=register).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.main_menu).pack()

    def login_screen(self):
        self.clear_window()
        tk.Label(self.root, text="Login", font=("Arial", 16)).pack(pady=10)

        tk.Label(self.root, text="Select Role").pack()
        role_var = tk.StringVar(value="patient")
        ttk.Combobox(self.root, textvariable=role_var, values=["patient", "doctor"], state="readonly").pack()

        tk.Label(self.root, text="Username").pack()
        username_entry = tk.Entry(self.root)
        username_entry.pack()
        tk.Label(self.root, text="Password").pack()
        password_entry = tk.Entry(self.root, show="*")
        password_entry.pack()

        def login():
            username = username_entry.get()
            password = password_entry.get()
            role = role_var.get()

            if role == "patient":
                c.execute("SELECT * FROM patients WHERE username = ? AND password = ?", (username, password))
            else:
                c.execute("SELECT * FROM doctors WHERE username = ? AND password = ?", (username, password))

            if c.fetchone():
                self.current_user = username
                self.user_role = role
                if role == "patient":
                    self.dashboard()
                else:
                    self.doctor_dashboard()
            else:
                messagebox.showerror("Error", "Invalid credentials")

        tk.Button(self.root, text="Login", command=login).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.main_menu).pack()

    def dashboard(self):
        self.clear_window()
        tk.Label(self.root, text=f"Welcome, {self.current_user}", font=("Arial", 14)).pack(pady=10)
        tk.Button(self.root, text="Book Appointment", command=self.book_appointment).pack(pady=5)
        tk.Button(self.root, text="View My Appointments", command=self.view_my_appointments).pack(pady=5)
        tk.Button(self.root, text="Search by Doctor/Date", command=self.search_appointments).pack(pady=5)
        tk.Button(self.root, text="Logout", command=self.main_menu).pack(pady=5)

    def book_appointment(self):
        self.clear_window()
        tk.Label(self.root, text="Book Appointment", font=("Arial", 14)).pack(pady=10)

        tk.Label(self.root, text="Select Doctor").pack()
        doctor_combo = ttk.Combobox(self.root, state="readonly")
        c.execute("SELECT username FROM doctors")
        doctors = [row[0] for row in c.fetchall()]
        doctor_combo["values"] = doctors
        doctor_combo.pack()

        tk.Label(self.root, text="Select Date").pack()
        cal = Calendar(self.root, selectmode='day')
        cal.pack(pady=5)

        tk.Label(self.root, text="Time (e.g., 10:00 AM)").pack()
        time_entry = tk.Entry(self.root)
        time_entry.pack()

        def save():
            doctor = doctor_combo.get()
            date = cal.get_date()
            time = time_entry.get()
            if doctor and date and time:
                c.execute("INSERT INTO appointments (patient_username, doctor, date, time) VALUES (?, ?, ?, ?)",
                          (self.current_user, doctor, date, time))
                conn.commit()
                messagebox.showinfo("Success", "Appointment booked successfully!")
                self.dashboard()
            else:
                messagebox.showerror("Error", "All fields required")

        tk.Button(self.root, text="Save Appointment", command=save).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.dashboard).pack()

    def view_my_appointments(self):
        self.clear_window()
        tk.Label(self.root, text="My Appointments", font=("Arial", 14)).pack(pady=10)
        tree = ttk.Treeview(self.root, columns=("ID", "Doctor", "Date", "Time"), show='headings')
        for col in tree["columns"]:
            tree.heading(col, text=col)
        tree.pack()

        c.execute("SELECT id, doctor, date, time FROM appointments WHERE patient_username = ?", (self.current_user,))
        for row in c.fetchall():
            tree.insert('', 'end', values=row)

        def delete_appointment():
            selected = tree.selection()
            if selected:
                appointment_id = tree.item(selected[0])['values'][0]
                c.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
                conn.commit()
                messagebox.showinfo("Deleted", "Appointment deleted")
                self.view_my_appointments()

        def reschedule_appointment():
            selected = tree.selection()
            if selected:
                appointment_id = tree.item(selected[0])['values'][0]
                top = tk.Toplevel(self.root)
                top.title("Reschedule Appointment")

                tk.Label(top, text="Select New Date").pack()
                cal = Calendar(top, selectmode='day')
                cal.pack(pady=5)

                tk.Label(top, text="New Time").pack()
                time_entry = tk.Entry(top)
                time_entry.pack()

                def update():
                    new_date = cal.get_date()
                    new_time = time_entry.get()
                    c.execute("UPDATE appointments SET date = ?, time = ? WHERE id = ?", (new_date, new_time, appointment_id))
                    conn.commit()
                    messagebox.showinfo("Success", "Appointment rescheduled")
                    top.destroy()
                    self.view_my_appointments()

                tk.Button(top, text="Update", command=update).pack(pady=5)

        tk.Button(self.root, text="Delete Appointment", command=delete_appointment).pack(pady=5)
        tk.Button(self.root, text="Reschedule Appointment", command=reschedule_appointment).pack(pady=5)
        tk.Button(self.root, text="Back", command=self.dashboard).pack(pady=10)

    def search_appointments(self):
        self.clear_window()
        tk.Label(self.root, text="Search Appointments", font=("Arial", 14)).pack(pady=10)
        tk.Label(self.root, text="Doctor Name or Date (e.g. 05/31/25)").pack()
        search_entry = tk.Entry(self.root)
        search_entry.pack()

        tree = ttk.Treeview(self.root, columns=("Doctor", "Date", "Time"), show='headings')
        for col in tree["columns"]:
            tree.heading(col, text=col)
        tree.pack()

        def search():
            value = search_entry.get()
            tree.delete(*tree.get_children())
            c.execute("SELECT doctor, date, time FROM appointments WHERE doctor LIKE ? OR date = ?",
                      (f"%{value}%", value))
            for row in c.fetchall():
                tree.insert('', 'end', values=row)

        tk.Button(self.root, text="Search", command=search).pack(pady=5)
        tk.Button(self.root, text="Back", command=self.dashboard).pack(pady=10)

    def doctor_dashboard(self):
        self.clear_window()
        tk.Label(self.root, text=f"Doctor Dashboard - Dr. {self.current_user}", font=("Arial", 14)).pack(pady=10)

        tree = ttk.Treeview(self.root, columns=("ID", "Patient", "Date", "Time"), show='headings')
        for col in tree["columns"]:
            tree.heading(col, text=col)
        tree.pack()

        c.execute("SELECT id, patient_username, date, time FROM appointments WHERE doctor = ?", (self.current_user,))
        for row in c.fetchall():
            tree.insert('', 'end', values=row)

        def delete_appointment():
            selected = tree.selection()
            if selected:
                appointment_id = tree.item(selected[0])['values'][0]
                c.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
                conn.commit()
                messagebox.showinfo("Deleted", "Appointment deleted")
                self.doctor_dashboard()

        tk.Button(self.root, text="Delete Appointment", command=delete_appointment).pack(pady=5)
        tk.Button(self.root, text="Logout", command=self.main_menu).pack(pady=10)

# -------------------- Run Application --------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = MedicalApp(root)
    root.geometry("600x550")
    root.mainloop()
