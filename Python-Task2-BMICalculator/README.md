# BMI Insight — Advanced BMI Calculator

A Python/Tkinter desktop application that calculates BMI, saves named users' measurements in SQLite, displays historical records, and plots a trend chart using Matplotlib.

## Advanced-tier feature checklist
- [x] Tkinter GUI (no command-line interaction for normal use).
- [x] Labeled name, weight (kg), and height (m) fields plus Calculate button.
- [x] BMI value and category shown with category-coloured feedback.
- [x] Multi-user support: records are grouped by user name.
- [x] Historical records saved in a local SQLite database.
- [x] User-selectable history table and Matplotlib line chart for BMI trends.
- [x] Input validation for empty, non-numeric, non-finite, zero, negative and unreasonable height values.
- [x] Database read/write errors are handled with GUI error messages.

## Run
Python 3.10+:

```bash
python -m pip install -r requirements.txt
python bmi_calculator.py
```

## Test
```bash
python -m unittest -v
```

## Data and privacy
Names and measurement records are stored locally in `bmi_records.db` beside the application. No data is sent to a server. Delete that database file to remove locally stored records.

## Important limitation
BMI is a general screening measure and does not diagnose health conditions. This project is for educational purposes, not medical advice.

## Implementation notes
- `calculate_bmi` is a pure function, separate from the GUI.
- `BMIStore` owns parameterized SQLite operations.
- `BMICalculatorApp` owns presentation and user interaction.
