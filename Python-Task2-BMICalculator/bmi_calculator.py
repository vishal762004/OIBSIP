
"""
Advanced BMI Calculator
Features:
- Tkinter graphical interface
- BMI calculation and categories
- SQLite database for saving records
- Multiple user support
- BMI history
- BMI trend chart
- User-friendly input validation
"""

from __future__ import annotations

import math
import sqlite3
import tkinter as tk

from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk


DB_PATH = Path(__file__).with_name("bmi_records.db")


# ==========================================
# BMI CALCULATION
# ==========================================

def calculate_bmi(weight_kg: float, height_m: float) -> tuple[float, str]:
    """Calculate BMI and return its category."""

    if not math.isfinite(weight_kg) or not math.isfinite(height_m):
        raise ValueError("Please enter valid numbers for weight and height.")

    if weight_kg <= 0:
        raise ValueError("Weight must be greater than zero.")

    if height_m <= 0:
        raise ValueError("Height must be greater than zero.")

    bmi_value = weight_kg / (height_m ** 2)

    if bmi_value < 18.5:
        category = "Underweight"
    elif bmi_value < 25:
        category = "Normal"
    elif bmi_value < 30:
        category = "Overweight"
    else:
        category = "Obese"

    return bmi_value, category


def is_valid_name(name: str) -> bool:
    """Accept letters, spaces, hyphens, apostrophes and dots (so Mary-Ann and O'Brien work)."""
    allowed_extra = " -'\u2019."
    return any(c.isalpha() for c in name) and all(c.isalpha() or c in allowed_extra for c in name)


def chart_points(records):
    """Turn history rows into (x positions, x labels, BMI values) for the trend chart.

    Each row is (bmi, category, "YYYY-MM-DDTHH:MM:SS"). The x position is the record
    number, so several records saved on the same day still show as separate points.
    """
    positions = list(range(1, len(records) + 1))
    labels = [row[2][5:].replace("T", " ") for row in records]   # "11-15 10:00:00"
    values = [row[0] for row in records]
    return positions, labels, values


# ==========================================
# DATABASE
# ==========================================

class BMIStore:
    """SQLite database for storing BMI records."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self._initialize()

    def _connect(self):
        """Open a new connection to the SQLite file."""
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        """Create the records table the first time the app runs."""
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS bmi_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT NOT NULL,
                    weight_kg REAL NOT NULL,
                    height_m REAL NOT NULL,
                    bmi REAL NOT NULL,
                    category TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                )
            """)

    def add(self, user_name, weight, height, bmi, category):
        """Save one measurement. The ? placeholders keep user input out of the SQL text."""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO bmi_records
                (user_name, weight_kg, height_m, bmi, category, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_name,
                    weight,
                    height,
                    bmi,
                    category,
                    datetime.now().isoformat(timespec="seconds")
                )
            )

    def users(self):
        """Return every saved user name, sorted without regard to capitals."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT user_name
                FROM bmi_records
                ORDER BY user_name COLLATE NOCASE
                """
            ).fetchall()

        return [row[0] for row in rows]

    def history(self, user_name):
        """Return (bmi, category, recorded_at) rows for one user, oldest first."""
        with self._connect() as connection:
            return connection.execute(
                """
                SELECT bmi, category, recorded_at
                FROM bmi_records
                WHERE user_name = ?
                ORDER BY recorded_at
                """,
                (user_name,)
            ).fetchall()


# ==========================================
# MAIN APPLICATION
# ==========================================

class BMICalculatorApp:

    def __init__(self, root):

        self.root = root
        self.root.title("BMI Insight | Advanced BMI Calculator")
        self.root.geometry("760x600")
        self.root.minsize(650, 520)

        # Initialize database
        try:
            self.store = BMIStore()
            self.store_error = None

        except (sqlite3.Error, OSError) as error:
            self.store = None
            self.store_error = str(error)

        self._build_ui()

        if self.store is None:
            messagebox.showerror(
                "Database Error",
                f"Could not initialize BMI storage:\n{self.store_error}"
            )
        else:
            self._refresh_users()

    # ======================================
    # BUILD USER INTERFACE
    # ======================================

    def _build_ui(self):

        style = ttk.Style()

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 20, "bold")
        )

        style.configure(
            "Result.TLabel",
            font=("Segoe UI", 15, "bold")
        )

        style.configure(
            "BMI.Normal.TLabel",
            foreground="#15803d",
            font=("Segoe UI", 15, "bold")
        )

        style.configure(
            "BMI.Underweight.TLabel",
            foreground="#b45309",
            font=("Segoe UI", 15, "bold")
        )

        style.configure(
            "BMI.Overweight.TLabel",
            foreground="#c2410c",
            font=("Segoe UI", 15, "bold")
        )

        style.configure(
            "BMI.Obese.TLabel",
            foreground="#b91c1c",
            font=("Segoe UI", 15, "bold")
        )

        container = ttk.Frame(self.root, padding=22)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="BMI INSIGHT",
            style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            container,
            text="Calculate, save and review your BMI history."
        ).pack(anchor="w", pady=(2, 18))

        # Input form
        form = ttk.LabelFrame(
            container,
            text="New Measurement",
            padding=14
        )

        form.pack(fill="x")

        self.name_var = tk.StringVar()
        self.weight_var = tk.StringVar()
        self.height_var = tk.StringVar()

        fields = [
            ("User Name", self.name_var, "Example: Alex"),
            ("Weight (kg)", self.weight_var, "Example: 68.5"),
            ("Height (m)", self.height_var, "Example: 1.72")
        ]

        for row, (label, variable, hint) in enumerate(fields):

            ttk.Label(
                form,
                text=label
            ).grid(
                row=row,
                column=0,
                sticky="w",
                padx=(0, 12),
                pady=6
            )

            ttk.Entry(
                form,
                textvariable=variable,
                width=28
            ).grid(
                row=row,
                column=1,
                sticky="ew",
                pady=6
            )

            ttk.Label(
                form,
                text=hint,
                foreground="#64748b"
            ).grid(
                row=row,
                column=2,
                sticky="w",
                padx=10
            )

        form.columnconfigure(1, weight=1)

        ttk.Button(
            form,
            text="Calculate and Save",
            command=self.calculate
        ).grid(
            row=3,
            column=1,
            sticky="e",
            pady=(12, 0)
        )

        # Result display
        self.result_var = tk.StringVar(
            value="Your result will appear here."
        )

        self.result_label = ttk.Label(
            container,
            textvariable=self.result_var,
            style="Result.TLabel"
        )

        self.result_label.pack(
            anchor="w",
            pady=18
        )

        # History section
        history_frame = ttk.LabelFrame(
            container,
            text="Saved History",
            padding=12
        )

        history_frame.pack(
            fill="both",
            expand=True
        )

        top = ttk.Frame(history_frame)
        top.pack(fill="x", pady=(0, 8))

        ttk.Label(
            top,
            text="Select User:"
        ).pack(side="left")

        self.user_combo = ttk.Combobox(
            top,
            state="readonly",
            width=25
        )

        self.user_combo.pack(
            side="left",
            padx=8
        )

        self.user_combo.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.show_history()
        )

        ttk.Button(
            top,
            text="Refresh",
            command=self._refresh_users
        ).pack(side="left")

        # History table
        columns = ("date", "bmi", "category")

        self.tree = ttk.Treeview(
            history_frame,
            columns=columns,
            show="headings",
            height=8
        )

        headings = [
            ("date", "Recorded At", 230),
            ("bmi", "BMI", 100),
            ("category", "Category", 160)
        ]

        for column, title, width in headings:

            self.tree.heading(
                column,
                text=title
            )

            self.tree.column(
                column,
                width=width,
                anchor="w"
            )

        self.tree.pack(
            fill="both",
            expand=True
        )

        ttk.Button(
            history_frame,
            text="View BMI Trend Chart",
            command=self.show_chart
        ).pack(
            anchor="e",
            pady=(10, 0)
        )

        ttk.Label(
            container,
            text="Note: BMI is a screening measure, not a medical diagnosis.",
            foreground="#64748b"
        ).pack(
            anchor="w",
            pady=(12, 0)
        )

    # ======================================
    # INPUT VALIDATION AND BMI CALCULATION
    # ======================================

    def calculate(self):
        """Read the form, validate every field, calculate the BMI, save it and refresh the screen."""

        if self.store is None:
            messagebox.showerror(
                "Database Unavailable",
                "BMI records cannot be saved because the database could not be initialized."
            )
            return

        # Get user name
        name = self.name_var.get().strip()

        # Validate name
        if not name:
            messagebox.showerror(
                "Invalid Name",
                "Please enter your name."
            )
            return

        if not is_valid_name(name):
            messagebox.showerror(
                "Invalid Name",
                "Name can contain only letters, spaces, hyphens and apostrophes.\n"
                "Numbers and other symbols are not allowed."
            )
            return

        # Get weight and height text
        weight_text = self.weight_var.get().strip()
        height_text = self.height_var.get().strip()

        # Validate empty weight
        if not weight_text:
            messagebox.showerror(
                "Invalid Weight",
                "Please enter your weight in kilograms."
            )
            return

        # Validate weight number
        try:
            weight = float(weight_text)

        except ValueError:
            messagebox.showerror(
                "Invalid Weight",
                "Weight must be a valid number.\n"
                "Example: 65 or 65.5"
            )
            return

        if not math.isfinite(weight):
            messagebox.showerror(
                "Invalid Weight",
                "Please enter a valid, finite weight."
            )
            return

        if weight <= 0:
            messagebox.showerror(
                "Invalid Weight",
                "Weight must be greater than 0 kg."
            )
            return

        if weight > 500:
            messagebox.showerror(
                "Invalid Weight",
                "Please enter a realistic weight.\n"
                "Maximum allowed weight is 500 kg."
            )
            return

        # Validate empty height
        if not height_text:
            messagebox.showerror(
                "Invalid Height",
                "Please enter your height in meters."
            )
            return

        # Validate height number
        try:
            height = float(height_text)

        except ValueError:
            messagebox.showerror(
                "Invalid Height",
                "Height must be a valid number.\n"
                "Example: 1.75"
            )
            return

        if not math.isfinite(height):
            messagebox.showerror(
                "Invalid Height",
                "Please enter a valid, finite height."
            )
            return

        if height <= 0:
            messagebox.showerror(
                "Invalid Height",
                "Height must be greater than 0."
            )
            return

        if not 0.5 <= height <= 2.7:
            messagebox.showerror(
                "Invalid Height",
                "Please enter your height between "
                "0.5 and 2.7 meters."
            )
            return

        # Calculate and save BMI
        try:

            bmi_value, category = calculate_bmi(
                weight,
                height
            )

            self.store.add(
                name,
                weight,
                height,
                bmi_value,
                category
            )

            self.result_var.set(
                f"BMI: {bmi_value:.2f}  |  Category: {category}"
            )

            self.result_label.configure(
                style=f"BMI.{category}.TLabel"
            )

            self._refresh_users(select=name)

            self.show_history()

        except ValueError as error:

            messagebox.showerror(
                "Calculation Error",
                str(error)
            )

        except (sqlite3.Error, OSError) as error:

            messagebox.showerror(
                "Storage Error",
                f"Could not save your record:\n{error}"
            )

    # ======================================
    # REFRESH USER LIST
    # ======================================

    def _refresh_users(self, select=None):
        """Reload the user drop-down; optionally select the user who just saved."""

        if self.store is None:
            return

        try:

            users = self.store.users()

            self.user_combo["values"] = users

            if select in users:
                self.user_combo.set(select)

            elif users and not self.user_combo.get():
                self.user_combo.set(users[0])

            if self.user_combo.get():
                self.show_history()

        except (sqlite3.Error, OSError) as error:

            messagebox.showerror(
                "Database Error",
                f"Could not load users:\n{error}"
            )

    # ======================================
    # SHOW BMI HISTORY
    # ======================================

    def show_history(self):
        """Fill the history table with the selected user's records."""

        for item in self.tree.get_children():
            self.tree.delete(item)

        user = self.user_combo.get()

        if not user or self.store is None:
            return

        try:

            records = self.store.history(user)

            for bmi_value, category, recorded_at in records:

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        recorded_at.replace("T", " "),
                        f"{bmi_value:.2f}",
                        category
                    )
                )

        except (sqlite3.Error, OSError) as error:

            messagebox.showerror(
                "Database Error",
                f"Could not load BMI history:\n{error}"
            )

    # ======================================
    # BMI TREND CHART
    # ======================================

    def show_chart(self):
        """Open a Matplotlib line chart of the selected user's BMI (needs 2+ records)."""

        user = self.user_combo.get()

        if self.store is None:
            messagebox.showerror(
                "Database Unavailable",
                "BMI history is unavailable because the database could not be initialized."
            )
            return

        if not user:
            messagebox.showinfo(
                "No History",
                "Save a BMI record first."
            )
            return

        try:

            records = self.store.history(user)

        except (sqlite3.Error, OSError) as error:

            messagebox.showerror(
                "Database Error",
                f"Could not read BMI history:\n{error}"
            )
            return

        if len(records) < 2:
            messagebox.showinfo(
                "Not Enough Data",
                "At least two saved records are needed for a trend chart."
            )
            return

        try:

            import matplotlib.pyplot as plt

            # One point per saved record (see chart_points for why).
            positions, labels, values = chart_points(records)

            plt.figure(figsize=(8, 4))
            plt.plot(positions, values, marker="o")
            plt.title(f"BMI History for {user}")
            plt.xlabel("Saved record (month-day time)")
            plt.ylabel("BMI")
            plt.xticks(positions, labels, rotation=30, ha="right")

            plt.grid(alpha=0.25)
            plt.tight_layout()
            plt.show()

        except ImportError:

            messagebox.showerror(
                "Missing Dependency",
                "Matplotlib is not installed.\n\n"
                "Install it using:\n"
                "python -m pip install matplotlib"
            )

        except Exception as error:

            messagebox.showerror(
                "Chart Error",
                f"Could not display the BMI chart:\n{error}"
            )


# ==========================================
# RUN APPLICATION
# ==========================================

def main():

    root = tk.Tk()

    BMICalculatorApp(root)

    root.mainloop()


if __name__ == "__main__":
    main()
