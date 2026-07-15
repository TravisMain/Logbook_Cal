# 🚗 Business Travel Logbook Generator

[![Live Web Generator](https://img.shields.io/badge/🚀%20Live%20Web%20App-Try%20Now%20In%20Browser-00C853?style=for-the-badge&logo=googlechrome&logoColor=white)](https://travismain.github.io/Logbook_Cal/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](file:///C:/Users/travism/source/repos/Logbook_Cal/LICENSE)

A complete, customizable suite for generating SARS & Corporate compliant travel logbook spreadsheets (`.xlsx`) with exact odometer reconciliation, smart detour variances, and configurable client destinations.

> 🌐 **Try it instantly online without installing anything:** [**https://travismain.github.io/Logbook_Cal/**](https://travismain.github.io/Logbook_Cal/)

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

### 2️⃣ Web Application (Run Live Online or Locally in Any Browser!)
You can use the Web Generator instantly right now in your browser without installing or downloading anything:
- 🌐 **Live Online Generator:** [**https://travismain.github.io/Logbook_Cal/**](https://travismain.github.io/Logbook_Cal/)

Or run it locally offline from your machine:
Navigate to the `web_app/` directory and open `index.html` in your web browser:
```bash
web_app/index.html
```
- Or simply double-click `index.html` from your file explorer.
- Features a premium, glassmorphic dark-mode UI with smart client clustering and automatic holiday/vacation scheduling.
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
        {"client": "Alpha Logistics / Client B", "count": 2}
    ],
    "clients": [
        {"name": "Acme Engineering Ltd", "one_way_km": 12, "frequency": "Very Frequent"},
        {"name": "Alpha Logistics / Client B", "one_way_km": 25, "frequency": "Very Frequent"},
        {"name": "Beta Enterprises / Client C", "one_way_km": 45, "frequency": "Regular"}
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

---

## ⚖️ Legal & Limitation of Liability Disclaimer

> [!CAUTION]
> **FOR EDUCATIONAL, RECONCILIATION, AND TEMPLATE PURPOSES ONLY**
> 
> By downloading, installing, running, or accessing this software (including the standalone CLI, Desktop GUI, or the online Web Generator hosted on GitHub Pages), **you explicitly acknowledge and agree to the following terms:**
> 
> 1. **No Responsibility or Liability**: The creator(s), author(s), and contributor(s) of this repository and software assume **ZERO RESPONSIBILITY OR LIABILITY** whatsoever for any financial, tax, legal, penal, audit, or statutory consequences arising from the use of this software, its formulas, or its generated Excel spreadsheets (`.xlsx`).
> 2. **Strictly Educational & Template Tool**: This application is provided solely as a mathematical template generator and educational reference tool to assist users in structuring and reconciling their odometer mileage and travel records. It does **NOT** constitute professional tax advice, accounting advice, or legal advice.
> 3. **User Responsibility & Verification**: You (the user) are **strictly and solely responsible** for verifying the accuracy, truthfulness, and legal compliance of any travel logbook, tax deduction claim (`ITR12`), or travel allowance document submitted to the **South African Revenue Service (SARS)**, any corporate employer, or any other tax authority globally.
> 4. **Compliance with Statutory Tax Laws**: Submitting fabricated, fraudulent, or inaccurate travel records to tax authorities is a statutory offense. You must ensure that every trip logged, odometer figure recorded, and destination claimed accurately reflects genuine business travel and verified vehicle history.
> 
> **IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, AUDIT PENALTIES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.**

---

## 📄 License

This project is open-source and licensed under the **[MIT License](file:///C:/Users/travism/source/repos/Logbook_Cal/LICENSE)**.  
See the `LICENSE` file for full terms, conditions, and liability disclaimers.
