"""SkyCast: a small desktop app that shows the CURRENT weather (OpenWeatherMap).

How it works:
1. WeatherService checks what you typed, calls the OpenWeatherMap "current weather"
   API and returns the data. It has no windows in it, so it is easy to test.
2. WeatherApp is the Tkinter window. Network calls run in a background thread so the
   window never freezes; the result is then drawn back on the main thread.

Not included: hourly or 5-day forecasts.
"""
from __future__ import annotations

import json
import os
import re
import threading
import tkinter as tk
from datetime import datetime
from io import BytesIO
from pathlib import Path
from tkinter import messagebox, simpledialog

import requests
from PIL import Image, ImageTk

CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
ICON_URL = "https://openweathermap.org/img/wn/{}@2x.png"
TIMEOUT_SECONDS = 12
CONFIG_DIR = Path(os.getenv("APPDATA", str(Path.home()))) / "SkyCast"
CONFIG_FILE = CONFIG_DIR / "config.json"


# ------------------------------------------------------------------
# Small helper functions
# ------------------------------------------------------------------
def celsius_to_fahrenheit(value):
    """Convert degrees Celsius to degrees Fahrenheit."""
    return value * 9 / 5 + 32


def temperature_text(value, unit):
    """Format a Celsius value for display in the chosen unit ('°C' or '°F')."""
    shown = celsius_to_fahrenheit(value) if unit == "°F" else value
    return f"{shown:.1f} {unit}"


def load_api_key():
    """Return the key saved on this computer, or the OPENWEATHER_API_KEY variable."""
    try:
        saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get("openweathermap_api_key", "")
    except (OSError, ValueError, AttributeError):
        saved = ""
    return saved or os.getenv("OPENWEATHER_API_KEY", "")


def save_api_key(key):
    """Save the key in the user's profile folder, never inside the project folder."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"openweathermap_api_key": key.strip()}, indent=2), encoding="utf-8")
    try:
        os.chmod(CONFIG_FILE, 0o600)   # owner-only access (limited effect on Windows)
    except OSError:
        pass


def _validate_payload(payload, required_keys, label):
    """Make sure the API answer is a dict containing every key the app needs."""
    if not isinstance(payload, dict) or any(key not in payload for key in required_keys):
        raise RuntimeError(f"OpenWeatherMap returned an incomplete {label} response.")


# ------------------------------------------------------------------
# Talking to the weather service (no windows here)
# ------------------------------------------------------------------
class WeatherService:
    def __init__(self, session=requests):
        # 'session' can be replaced by a fake in tests, so no internet is needed.
        self.session = session

    @staticmethod
    def _location_params(location):
        """Turn the typed text into API parameters, or raise ValueError with advice."""
        value = location.strip()
        if not value:
            raise ValueError("Enter a city or place name, for example Lucknow, Uttar Pradesh, IN.")

        # Two capital letters (like UP) are usually a state, not a precise place.
        if re.fullmatch(r"[A-Z]{2}", value):
            raise ValueError(
                f"'{value}' looks like a state abbreviation. Enter a city or full place name instead, "
                "for example Lucknow, Uttar Pradesh, IN."
            )
        if re.fullmatch(r"\d+", value):
            raise ValueError(
                "A number alone is not enough. For a postal code, include the country code, "
                "for example 110001,IN. Otherwise enter a city name."
            )
        if re.fullmatch(r"\d+[A-Za-z]+", value):
            raise ValueError(
                "That location looks invalid. Enter a city/place name or a postal code with country code, "
                "for example 110001,IN."
            )

        # Postal code such as "110001,IN" -> use the API's zip parameter.
        first_part = value.split(",", 1)[0].strip()
        if first_part.isdigit():
            if "," not in value:
                raise ValueError("For a postal code, add the country code, for example 110001,IN.")
            parts = [part.strip() for part in value.split(",")]
            if len(parts) != 2 or not re.fullmatch(r"[A-Za-z]{2}", parts[1]):
                raise ValueError("Use postal-code format like 110001,IN (two-letter country code).")
            return {"zip": f"{parts[0]},{parts[1].upper()}"}

        return {"q": value}   # ordinary city / place search

    def _get_json(self, url, params, label):
        """GET a URL and return its JSON; turn every failure into a friendly message."""
        try:
            response = self.session.get(url, params=params, timeout=TIMEOUT_SECONDS)
            if response.status_code == 401:
                raise RuntimeError("Invalid or inactive OpenWeatherMap API key. Open Settings to replace it, or wait for activation.")
            if response.status_code == 404:
                raise ValueError("Location not found. Try a city and country, such as Jaipur,IN.")
            if response.status_code == 429:
                raise RuntimeError("The weather service request limit was reached. Please wait and try again.")
            if response.status_code == 400:
                raise ValueError("The location search was not accepted. Check the spelling and try a city name or postal code with country code.")
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise RuntimeError(f"The service returned invalid {label} data.")
            return data
        except requests.Timeout as error:
            raise RuntimeError("The request timed out. Check your internet and try again.") from error
        except requests.ConnectionError as error:
            raise RuntimeError("Couldn't connect. Check your internet connection.") from error
        except requests.HTTPError as error:
            raise RuntimeError(f"Weather service error: {error}") from error
        except requests.RequestException as error:
            raise RuntimeError("A network error occurred while contacting the weather service. Please try again.") from error

    def get_weather(self, location, api_key):
        """Return {"current": <API data>} for a place, or raise ValueError / RuntimeError."""
        if not api_key or not api_key.strip():
            raise ValueError("Set your OpenWeatherMap API key in Settings first.")
        params = {**self._location_params(location), "appid": api_key.strip(), "units": "metric"}
        current = self._get_json(CURRENT_URL, params, "current weather")
        _validate_payload(current, ("name", "main", "wind", "weather"), "current weather")
        _validate_payload(current["main"], ("temp", "feels_like"), "temperature")
        if not current["weather"]:
            raise RuntimeError("No weather condition was returned for this place.")
        return {"current": current}

    def fetch_icon(self, icon_code):
        """Download the weather icon and return its bytes, or None (the icon is optional)."""
        try:
            response = self.session.get(ICON_URL.format(icon_code), timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.content
        except requests.RequestException:
            return None


# ------------------------------------------------------------------
# The window
# ------------------------------------------------------------------
class WeatherApp:
    BG = "#0b1220"
    PANEL = "#151f32"
    PANEL2 = "#1d2a40"
    HERO_BG = "#17314b"
    BORDER = "#263750"
    TEXT = "#edf4ff"
    MUTED = "#a9b8cf"
    ACCENT = "#54c7ec"

    def __init__(self, root):
        self.root = root
        root.title("SkyCast | Weather, made simple")
        root.geometry("900x650")
        root.minsize(700, 560)
        root.configure(bg=self.BG)

        self.service = WeatherService()
        self.api_key = load_api_key()
        self.unit_var = tk.StringVar(value="°C")
        self.location_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Search for a city to see its latest weather.")

        self.current_values = None   # the last weather result
        self.icon_bytes = None       # raw image bytes of the last icon
        self.icon_cache = {}         # icon code -> bytes, so each icon is downloaded once
        self.icon_ref = None         # Tk forgets images unless we keep a reference

        self._build_ui()
        self.root.after(400, self._first_run_setup)

    def _label(self, parent, text, size=10, bold=False, fg=None, bg=None, **options):
        """Create a Label with the app's font and colours."""
        font = ("Segoe UI", size, "bold") if bold else ("Segoe UI", size)
        return tk.Label(parent, text=text, bg=bg or self.PANEL, fg=fg or self.TEXT, font=font, **options)

    def _build_ui(self):
        """Create every widget: header, search box, big temperature card, 4 stat cards."""
        main = tk.Frame(self.root, bg=self.BG)
        main.pack(fill="both", expand=True, padx=26, pady=22)

        # Header: title on the left, Settings button on the right.
        header = tk.Frame(main, bg=self.BG)
        header.pack(fill="x")
        self._label(header, "☁  SKYCAST", 25, True, bg=self.BG).pack(side="left")
        self._label(header, "WEATHER, MADE SIMPLE", 9, True, fg=self.ACCENT, bg=self.BG).pack(side="left", padx=16, pady=(10, 0))
        tk.Button(
            header, text="⚙  Settings", command=self.configure_key, bg=self.PANEL2, fg=self.TEXT,
            activebackground="#30445f", activeforeground=self.TEXT, relief="flat", padx=14, pady=8, cursor="hand2",
        ).pack(side="right")
        self._label(main, "Look up the current weather for any place.", 11, fg=self.MUTED, bg=self.BG).pack(anchor="w", pady=(3, 18))

        # Search box: type a place and press Enter or click the button.
        search = tk.Frame(main, bg=self.PANEL, highlightbackground=self.BORDER, highlightthickness=1)
        search.pack(fill="x", pady=(0, 16))
        self._label(search, "LOCATION", 8, True, fg=self.MUTED).pack(anchor="w", padx=15, pady=(11, 3))
        row = tk.Frame(search, bg=self.PANEL)
        row.pack(fill="x", padx=12, pady=(0, 12))
        entry = tk.Entry(
            row, textvariable=self.location_var, bg=self.PANEL2, fg=self.TEXT,
            insertbackground=self.TEXT, relief="flat", font=("Segoe UI", 12),
        )
        entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 10))
        entry.bind("<Return>", lambda event: self.fetch_weather())
        tk.Button(
            row, text="Search weather  →", command=self.fetch_weather, bg=self.ACCENT, fg="#061522",
            activebackground="#8be0f5", relief="flat", font=("Segoe UI", 10, "bold"), padx=18, pady=10, cursor="hand2",
        ).pack(side="right")

        # Place name on the left, °C / °F switch on the right.
        toolbar = tk.Frame(main, bg=self.BG)
        toolbar.pack(fill="x", pady=(0, 8))
        self.place_label = self._label(toolbar, "Your weather overview", 16, True, bg=self.BG)
        self.place_label.pack(side="left")
        units = tk.Frame(toolbar, bg=self.BG)
        units.pack(side="right")
        for unit in ("°C", "°F"):
            tk.Radiobutton(
                units, text=unit, value=unit, variable=self.unit_var, command=self.refresh_display,
                bg=self.BG, fg=self.TEXT, selectcolor=self.PANEL2, activebackground=self.BG,
                activeforeground=self.TEXT, font=("Segoe UI", 10),
            ).pack(side="left", padx=4)

        # Big card: condition, temperature, feels-like and the weather icon.
        hero = tk.Frame(main, bg=self.HERO_BG, highlightbackground="#2c5873", highlightthickness=1)
        hero.pack(fill="x", pady=(0, 14))
        left = tk.Frame(hero, bg=self.HERO_BG)
        left.pack(side="left", fill="both", expand=True, padx=22, pady=18)
        self.condition_label = self._label(left, "Search a city to get started", 14, True, bg=self.HERO_BG)
        self.condition_label.pack(anchor="w")
        self.temp_label = self._label(left, "--°", 42, True, bg=self.HERO_BG)
        self.temp_label.pack(anchor="w", pady=(5, 0))
        self.feels_label = self._label(left, "Feels like --", 10, fg="#c5d9eb", bg=self.HERO_BG)
        self.feels_label.pack(anchor="w")
        self.icon_label = self._label(hero, "☀", 56, fg="#ffe39a", bg=self.HERO_BG)
        self.icon_label.pack(side="right", padx=35)

        # Four small cards; self.stat_labels[0..3] = humidity, wind, pressure, visibility.
        stats = tk.Frame(main, bg=self.BG)
        stats.pack(fill="x", pady=(0, 14))
        self.stat_labels = []
        for title, symbol in (("HUMIDITY", "💧"), ("WIND SPEED", "➤"), ("PRESSURE", "◉"), ("VISIBILITY", "◎")):
            card = tk.Frame(stats, bg=self.PANEL, highlightbackground=self.BORDER, highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=(0, 8))
            self._label(card, f"{symbol}  {title}", 8, True, fg=self.MUTED).pack(anchor="w", padx=12, pady=(12, 5))
            value = self._label(card, "--", 17, True)
            value.pack(anchor="w", padx=12, pady=(0, 12))
            self.stat_labels.append(value)

        # Status line (progress and error messages appear here, inside the window).
        self.status_label = tk.Label(main, textvariable=self.status_var, bg=self.BG, fg=self.MUTED, font=("Segoe UI", 9), anchor="w")
        self.status_label.pack(fill="x", pady=(18, 0))
        self._label(main, "Live current conditions powered by OpenWeatherMap", 8, fg="#71839d", bg=self.BG).pack(anchor="w", pady=(6, 0))

    # ---------------- API key ----------------
    def _first_run_setup(self):
        """On the very first run (no saved key) ask for the key."""
        if not self.api_key:
            self.configure_key(first_run=True)

    def configure_key(self, first_run=False):
        """Ask for the API key in a dialog and save it on this computer."""
        if first_run:
            title = "SkyCast setup"
            prompt = "Enter your OpenWeatherMap API key once. SkyCast will save it locally on this computer:"
        else:
            title = "API settings"
            prompt = "Enter or replace your OpenWeatherMap API key:"
        key = simpledialog.askstring(title, prompt, parent=self.root, show="*")
        if key and key.strip():
            self.api_key = key.strip()
            try:
                save_api_key(self.api_key)
                self.status_var.set("API key saved on this computer. Now search for a city.")
            except OSError as error:
                messagebox.showerror("Could not save key", f"SkyCast could not save the key: {error}\nYou can set OPENWEATHER_API_KEY in your environment instead.")
        elif first_run:
            self.status_var.set("API key setup is needed before you can search for weather. Use Settings when ready.")

    # ---------------- searching ----------------
    def fetch_weather(self):
        """Start a search. The slow network work happens in a background thread."""
        location = self.location_var.get().strip()
        if not location:
            self.status_var.set("Please enter a city or place name.")
            self.status_label.configure(fg="#ff9b9b")
            return
        if not self.api_key:
            self.configure_key(first_run=True)
        if not self.api_key:
            return
        self.status_var.set(f"Fetching weather for {location}…")
        self.status_label.configure(fg=self.ACCENT)
        threading.Thread(target=self._fetch_worker, args=(location, self.api_key), daemon=True).start()

    def _fetch_worker(self, location, key):
        """Runs in the background thread: network only. Windows are touched via root.after."""
        try:
            result = self.service.get_weather(location, key)
            icon_bytes = self._get_icon_bytes(result["current"]["weather"][0].get("icon", ""))
            self.root.after(0, lambda: self._render_result(result, icon_bytes))
        except (ValueError, RuntimeError) as error:
            message = str(error)
            self.root.after(0, lambda: self._show_error(message))
        except Exception as error:   # last safety net so the status line never stays stuck on "Fetching…"
            message = f"Unexpected problem: {error}"
            self.root.after(0, lambda: self._show_error(message))

    def _get_icon_bytes(self, icon_code):
        """Return icon bytes from the cache, downloading only the first time."""
        if not icon_code:
            return None
        if icon_code not in self.icon_cache:
            data = self.service.fetch_icon(icon_code)
            if data is None:
                return None
            self.icon_cache[icon_code] = data
        return self.icon_cache[icon_code]

    # ---------------- drawing the result ----------------
    def _show_error(self, message):
        """Show an error in the status line (inside the window, not the terminal)."""
        self.status_var.set(message)
        self.status_label.configure(fg="#ff9b9b")

    def _render_result(self, result, icon_bytes):
        """Store the new result, then draw it."""
        self.current_values = result
        self.icon_bytes = icon_bytes
        current = result["current"]
        country = current.get("sys", {}).get("country", "")
        self.place_label.configure(text=f"{current['name']}, {country}" if country else current["name"])
        self.refresh_display()
        self.status_var.set(f"Updated successfully at {datetime.now().strftime('%H:%M:%S')}.")
        self.status_label.configure(fg="#8be0ad")

    def refresh_display(self):
        """Redraw all numbers in the chosen unit. Makes NO network calls (also used by °C/°F)."""
        if not self.current_values:
            return
        current = self.current_values["current"]
        main = current["main"]
        unit = self.unit_var.get()
        self.condition_label.configure(text=current["weather"][0].get("description", "Conditions").title())
        self.temp_label.configure(text=temperature_text(main["temp"], unit))
        self.feels_label.configure(text=f"Feels like {temperature_text(main['feels_like'], unit)}")
        visibility = current.get("visibility")
        self.stat_labels[0].configure(text=f"{main.get('humidity', '--')}%")
        self.stat_labels[1].configure(text=f"{current.get('wind', {}).get('speed', 0):g} m/s")
        self.stat_labels[2].configure(text=f"{main.get('pressure', '--')} hPa")
        self.stat_labels[3].configure(text=f"{visibility / 1000:.1f} km" if visibility is not None else "--")
        self._show_icon()

    def _show_icon(self):
        """Show the cached icon image, or a cloud symbol if there is none."""
        if not self.icon_bytes:
            self.icon_label.configure(image="", text="☁")
            return
        try:
            image = Image.open(BytesIO(self.icon_bytes)).convert("RGBA")
            image.thumbnail((110, 110))
            self.icon_ref = ImageTk.PhotoImage(image)
            self.icon_label.configure(image=self.icon_ref, text="")
        except OSError:
            self.icon_label.configure(image="", text="☁")


def main():
    root = tk.Tk()
    WeatherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
