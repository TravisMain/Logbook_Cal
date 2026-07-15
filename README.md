# 🚗 Business Travel Logbook Generator

A complete, customizable suite for generating SARS & Corporate compliant travel logbook spreadsheets (`.xlsx`) with exact odometer reconciliation, smart detour variances, and configurable client destinations.

---

## ✨ Features
- **Exact Target Matching**: Automatically distributes trips and balances detour/shortcut variances (`±2 km` return) to hit your exact `Opening Odometer`, `Closing Odometer`, and `Total Business km` target.
- **Whole Integer Mode**: Option to enforce pure whole integer kilometers (`#,##0`) everywhere — no decimals appear anywhere across distances, odometer readings, or private gap calculations!
- **Holiday & Weekend Intelligence**: Automatically skips dates during configured holidays (e.g., Mauritius break) and correctly assigns Saturday trips when configured.
- **Professional Two-Sheet Excel Output**: Creates a beautifully formatted workbook with:
  1. **Cover Sheet**: Summary table, business/private usage percentages, and full destination frequency breakdown.
  2. **Business Logbook Sheet**: Complete chronological running odometer ledger with standard Excel formulas (`SUM`).

---

## 🖥️ How to Use (Three Ways!)

### 1️⃣ Graphical Desktop GUI Application (Recommended for Desktop Users)
Run the user-friendly graphical application:
```bash
python logbook_gui.py
```
- Enter your start and end dates, opening and closing odometers, and target business km.
- Add or remove destinations and set their frequency category (`Very Frequent`, `Frequent`, `Regular`, `Occasional`, `Rare`).
- Click **"✨ Generate & Save Logbook Excel (.xlsx)"** to choose where to save your spreadsheet and open it instantly!

---

### 2️⃣ Standalone Web Application (Runs in Any Browser — No Python Needed!)
Navigate to the `web_app/` directory and open `index.html` in your web browser:
```bash
web_app/index.html
```
- Or simply double-click `index.html` from your file explorer.
- Features a premium, glassmorphic dark-mode UI.
- Uses `SheetJS` directly inside your web browser to calculate trips and download the Excel file (`.xlsx`) instantly.

---

### 3️⃣ Interactive CLI & Configuration Mode (For Terminal & Automation)
Run the command-line tool with interactive prompts or a JSON config file:
```bash
# Interactive mode (prompts you in the terminal)
python generate_logbook_cli.py -i

# Config-driven mode (using config.json)
python generate_logbook_cli.py --config config.json --output My_Logbook.xlsx
```

#### Customizing `config.json`
You can edit `config.json` directly to store custom templates for different staff or tax years:
```json
{
    "start_date": "2025-03-01",
    "end_date": "2026-02-28",
    "opening_odo": 36950,
    "closing_odo": 53380,
    "target_business_km": 6080,
    "round_numbers_only": true,
    "holidays": [
        {"start": "2025-07-01", "end": "2025-07-14", "reason": "Annual Holiday"}
    ],
    "saturdays": [
        {"client": "Coke Devlin", "count": 2}
    ],
    "clients": [
        {"name": "Full Swing Engineering", "one_way_km": 7, "frequency": "Very Frequent"},
        {"name": "Coke Devlin", "one_way_km": 17, "frequency": "Very Frequent"}
    ]
}
```

---

## 📂 Project Structure
```
Logbook_Cal/
├── logbook_gui.py            # Desktop Graphical User Interface (Tkinter)
├── generate_logbook_cli.py   # Interactive & Config-driven Command Line Tool
├── logbook_engine.py         # Core mathematical trip & odometer generator
├── export_excel.py           # openpyxl two-sheet formatting and styling engine
├── config.json               # Default configuration & destination template
├── web_app/                  # Standalone Browser Application
│   ├── index.html            # UI Structure
│   ├── style.css             # Glassmorphic Styling
│   └── app.js                # SheetJS Client-side Engine
└── README.md                 # Documentation
```
