"""Advanced password generator with Tkinter, secrets, strength feedback and clipboard support."""

from __future__ import annotations

import secrets
import string
import tkinter as tk
from tkinter import messagebox, ttk

import pyperclip

AMBIGUOUS = set("0O1lI")
CHARACTER_GROUPS = {
    "uppercase": string.ascii_uppercase,
    "lowercase": string.ascii_lowercase,
    "digits": string.digits,
    "symbols": "!@#$%^&*()-_=+[]{};:,.?/|~",
}


def generate_password(length: int, selected_types: list[str], exclude_ambiguous: bool = False) -> str:
    """Generate a cryptographically strong password satisfying every selected type."""
    if not isinstance(length, int) or not 8 <= length <= 128:
        raise ValueError("Password length must be between 8 and 128 characters.")
    groups = [CHARACTER_GROUPS[name] for name in selected_types if name in CHARACTER_GROUPS]
    if len(groups) < 2:
        raise ValueError("Select at least two character types.")
    if exclude_ambiguous:
        groups = ["".join(char for char in group if char not in AMBIGUOUS) for group in groups]
    if any(not group for group in groups):
        raise ValueError("One selected character type has no available characters.")

    # Guarantee one character from every selected group before filling remaining slots.
    password_chars = [secrets.choice(group) for group in groups]
    alphabet = "".join(groups)
    password_chars.extend(secrets.choice(alphabet) for _ in range(length - len(password_chars)))

    # A cryptographically secure shuffle avoids predictable group positions.
    for index in range(len(password_chars) - 1, 0, -1):
        swap_index = secrets.randbelow(index + 1)
        password_chars[index], password_chars[swap_index] = password_chars[swap_index], password_chars[index]
    return "".join(password_chars)


def estimate_strength(length: int, type_count: int) -> tuple[str, str]:
    """Return a simple educational strength label and explanatory note."""
    # Very long passwords stay strong even with only two character types.
    if (length >= 16 and type_count >= 3) or (length >= 24 and type_count >= 2):
        return "Strong", "Long password with good character diversity."
    if length >= 12 and type_count >= 2:
        return "Medium", "Reasonable length; consider more character types."
    return "Weak", "Increase length and character diversity."


class PasswordGeneratorApp:
    def __init__(self, root: tk.Tk):
        """Set up the window state: option variables, the session history and the hidden flag."""
        self.root = root
        self.root.title("CipherCraft | Secure Password Generator")
        self.root.geometry("620x570")
        self.root.minsize(540, 500)
        self.length_var = tk.IntVar(value=18)
        self.ambiguous_var = tk.BooleanVar(value=True)
        self.type_vars = {name: tk.BooleanVar(value=(name != "symbols")) for name in CHARACTER_GROUPS}
        self.password_var = tk.StringVar()
        self.strength_var = tk.StringVar(value="Generate a password to see its strength.")
        self.history: list[str] = []   # newest first, last 5 only, never saved to disk
        self.hidden = False            # True while the password is masked with dots
        self._build_ui()

    def _build_ui(self):
        """Create every label, checkbox, button and list in the window."""
        frame = ttk.Frame(self.root, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="CIPHERCRAFT", font=("Segoe UI", 21, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Generate strong passwords using Python's secure secrets module.",
                  foreground="#64748b").pack(anchor="w", pady=(2, 18))

        settings = ttk.LabelFrame(frame, text="Password settings", padding=14)
        settings.pack(fill="x")
        ttk.Label(settings, text="Length (8–128)").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(settings, from_=8, to=128, textvariable=self.length_var, width=8).grid(
            row=0, column=1, sticky="w", padx=12
        )
        ttk.Label(settings, text="Character types").grid(row=1, column=0, sticky="nw", pady=(14, 0))
        checks = ttk.Frame(settings)
        checks.grid(row=1, column=1, sticky="w", pady=(10, 0))
        labels = [("uppercase", "Uppercase A–Z"), ("lowercase", "Lowercase a–z"),
                  ("digits", "Numbers 0–9"), ("symbols", "Symbols")]
        for index, (key, label) in enumerate(labels):
            ttk.Checkbutton(checks, text=label, variable=self.type_vars[key]).grid(
                row=index // 2, column=index % 2, sticky="w", padx=(0, 18), pady=3
            )
        ttk.Checkbutton(settings, text="Exclude ambiguous characters (0, O, 1, l, I)",
                        variable=self.ambiguous_var).grid(row=2, column=1, sticky="w", pady=(12, 0))

        ttk.Button(frame, text="Generate secure password", command=self.generate).pack(anchor="w", pady=16)
        result = ttk.LabelFrame(frame, text="Your password", padding=14)
        result.pack(fill="x")
        self.password_entry = ttk.Entry(result, textvariable=self.password_var, font=("Consolas", 13), state="readonly")
        self.password_entry.pack(fill="x", pady=(0, 10))
        buttons = ttk.Frame(result)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Copy to clipboard", command=self.copy_password).pack(side="left")
        ttk.Button(buttons, text="Show / hide", command=self.toggle_visibility).pack(side="left", padx=8)
        ttk.Label(result, textvariable=self.strength_var, wraplength=500).pack(anchor="w", pady=(12, 0))
        self.clipboard_status_var = tk.StringVar(value="")
        ttk.Label(result, textvariable=self.clipboard_status_var, foreground="#64748b").pack(anchor="w", pady=(4, 0))

        history_frame = ttk.LabelFrame(frame, text="Recent session history (last 5)", padding=12)
        history_frame.pack(fill="both", expand=True, pady=(16, 0))
        self.history_list = tk.Listbox(history_frame, height=5, font=("Consolas", 10))
        self.history_list.pack(fill="both", expand=True)
        ttk.Label(frame, text="Passwords are kept only in this running session; they are never written to disk.",
                  foreground="#64748b", wraplength=560).pack(anchor="w", pady=(12, 0))

    def generate(self):
        """Read the settings, create a password, show it, store it in history and copy it."""
        try:
            # IntVar.get() raises TclError if the Spinbox holds text; handled below.
            length = self.length_var.get()
            selected = [name for name, variable in self.type_vars.items() if variable.get()]
            password = generate_password(length, selected, self.ambiguous_var.get())
            self.password_var.set(password)
            self.history.insert(0, password)
            self.history = self.history[:5]
            self._refresh_history()
            label, explanation = estimate_strength(length, len(selected))
            self.strength_var.set(f"Strength: {label} — {explanation}")
            # Use pyperclip as specified by the internship task. A clipboard issue
            # must not discard a password that was generated successfully.
            try:
                pyperclip.copy(password)
                self.clipboard_status_var.set("Automatically copied to clipboard.")
            except pyperclip.PyperclipException:
                self.clipboard_status_var.set("Clipboard unavailable; use the Copy button after enabling a clipboard provider.")
        except (ValueError, tk.TclError) as error:
            messagebox.showerror("Cannot generate password", str(error))

    def copy_password(self):
        """Copy the shown password again; explain clearly if the clipboard is unavailable."""
        password = self.password_var.get()
        if not password:
            messagebox.showinfo("Nothing to copy", "Generate a password first.")
            return
        try:
            pyperclip.copy(password)
            self.clipboard_status_var.set("Copied to clipboard.")
            messagebox.showinfo("Copied", "Password copied to clipboard.")
        except pyperclip.PyperclipException:
            messagebox.showerror("Clipboard unavailable", "Install or enable a clipboard provider for pyperclip, then try again.")

    def toggle_visibility(self):
        """Hide or show the password AND the history list together."""
        self.hidden = not self.hidden
        self.password_entry.configure(show="\u2022" if self.hidden else "")
        self._refresh_history()

    def _refresh_history(self):
        """Redraw the last-5 list, masking each entry while the hidden flag is on."""
        self.history_list.delete(0, tk.END)
        for item in self.history:
            self.history_list.insert(tk.END, "\u2022" * len(item) if self.hidden else item)


def main():
    root = tk.Tk()
    PasswordGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
