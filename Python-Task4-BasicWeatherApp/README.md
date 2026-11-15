# SkyCast — Current Weather App

A focused Tkinter desktop weather app that searches a city or postal code and displays current conditions only. The hourly and five-day forecast panels have been intentionally removed to keep the interface simple.

## Features
- Modern dark dashboard with city/place search.
- No API-key field on the main screen: enter your OpenWeatherMap key once in the first-run setup dialog or later through **Settings**.
- The key is stored locally in your Windows user profile at `%APPDATA%\SkyCast\config.json`, not in the project folder or source code. This is convenient for a personal desktop app, but it is not a secure secret vault. Do not publish that config file or distribute a desktop build containing your key. For a public multi-user deployment, put API calls behind a secured backend.
- Current temperature, feels-like temperature, condition icon, humidity, wind, pressure and visibility.
- Celsius/Fahrenheit switch (no new download needed), Enter-to-search, background network requests (the window does not freeze), the weather icon is downloaded once and cached, and actionable errors shown inside the window.
- Not included: hourly forecast and 5-day forecast panels.
- City/place search (e.g. `Delhi,IN`, `Mumbai,IN`, `New York,US`) and postal-code search (e.g. `110001,IN`). Rejects blank input, state-only abbreviations such as `UP`, numeric-only input, malformed numeric words, and invalid postal-code formats with helpful guidance; unknown places show a not-found message.

## API setup (once per computer)
1. Create a free account at https://home.openweathermap.org/users/sign_up.
2. Open **API keys** and copy an active key. New keys can take time to activate.
3. Launch SkyCast. On first run, paste the key into the one-time setup dialog. Later, use **Settings** to replace it.
4. The main screen never asks for the key during normal weather searches.

The app uses the OpenWeatherMap Current Weather endpoint only.

## Install and run
Python 3.10+:
```bash
python -m pip install -r requirements.txt
python weather_app.py
```

Optional environment-variable setup:
```powershell
$env:OPENWEATHER_API_KEY="YOUR_API_KEY_HERE"
python weather_app.py
```

## Tests
```bash
python -m unittest -v
```
Tests mock HTTP responses and do not require a live key. Also launch the GUI yourself and capture a genuine live demo before submission.

## Data and privacy
The city/place query and API key are sent to OpenWeatherMap. The app does not request device location. The saved key is stored in a local per-user JSON configuration file; keep it private and out of GitHub, screenshots and LinkedIn.

## API documentation
- https://openweathermap.org/current
- https://openweathermap.org/weather-conditions
- https://openweathermap.org/appid
