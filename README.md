# OIBSIP — Python Programming Track

Three Python tasks from the Oasis Infobyte SIP task list, each in its own folder.

| Folder | What it is | Tier |
|--------|-----------|------|
| `Python-Task2-BMICalculator` | Tkinter BMI calculator with SQLite history for several users and a Matplotlib trend chart | Advanced checklist items covered |
| `Python-Task3-RandomPasswordGenerator` | Tkinter password generator using `secrets`, strength label, ambiguous-character option, `pyperclip` copy, last-5 session history | Advanced checklist items covered |
| `Python-Task4-BasicWeatherApp` | Tkinter app showing the **current** weather (city or postal code), °C/°F switch and icon. **No hourly or 5-day forecast.** | Beginner checklist plus a GUI |

Each folder has its own README, `requirements.txt` and unit tests.

## Requirements
- Python 3.10 or newer, with Tkinter (included with the normal Windows installer).
- Install each project's packages from its own `requirements.txt`.
- The Weather App needs your own free OpenWeatherMap API key (see its README). Never upload the key.

## Run a project
```bash
cd Python-Task3-RandomPasswordGenerator
python -m pip install -r requirements.txt
python password_generator.py
```

## Run the tests
From inside a project folder (after installing its requirements):
```bash
python -m unittest -v
```
The tests cover the logic only. The windows must be tested by hand.

## Screenshots
Add real screenshots of each running app to its folder before submitting.
