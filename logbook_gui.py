#!/usr/bin/env python3
"""
Desktop Graphical User Interface (GUI) for Business Travel Logbook Generator
Run: python logbook_gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import subprocess
from logbook_engine import LogbookEngine
from export_excel import export_logbook_to_excel

class LogbookGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🚗 Business Travel Logbook Generator — Excel Export Tool")
        self.geometry("820x680")
        self.minsize(760, 600)
        
        # Configure style
        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")
        
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#1F4E79")
        self.style.configure("Sub.TLabel", font=("Segoe UI", 9, "italic"), foreground="#555555")
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        self.style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"), foreground="white", background="#1F4E79", padding=8)

        self.create_widgets()
        self.load_default_config()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(header_frame, text="🚗 Business Travel Logbook Generator", style="Header.TLabel").pack(anchor="w")
        ttk.Label(header_frame, text="Enter your date period, odometer readings, and destinations below to automatically generate an exact Excel logbook.", style="Sub.TLabel").pack(anchor="w")

        # Top section: General Settings
        settings_frame = ttk.LabelFrame(main_frame, text=" 1. Trip & Vehicle Parameters ", padding=12)
        settings_frame.pack(fill=tk.X, pady=(0, 15))

        # Grid inside settings
        ttk.Label(settings_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", pady=4, padx=(0,10))
        self.start_date_var = tk.StringVar(value="")
        ttk.Entry(settings_frame, textvariable=self.start_date_var, width=15).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(settings_frame, text="End Date (YYYY-MM-DD):").grid(row=0, column=2, sticky="w", pady=4, padx=(20,10))
        self.end_date_var = tk.StringVar(value="")
        ttk.Entry(settings_frame, textvariable=self.end_date_var, width=15).grid(row=0, column=3, sticky="w", pady=4)

        ttk.Label(settings_frame, text="Opening Odometer (km):").grid(row=1, column=0, sticky="w", pady=4, padx=(0,10))
        self.open_odo_var = tk.StringVar(value="0")
        ttk.Entry(settings_frame, textvariable=self.open_odo_var, width=15).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(settings_frame, text="Closing Odometer (km):").grid(row=1, column=2, sticky="w", pady=4, padx=(20,10))
        self.close_odo_var = tk.StringVar(value="0")
        ttk.Entry(settings_frame, textvariable=self.close_odo_var, width=15).grid(row=1, column=3, sticky="w", pady=4)

        ttk.Label(settings_frame, text="Target Business km:").grid(row=2, column=0, sticky="w", pady=4, padx=(0,10))
        self.biz_km_var = tk.StringVar(value="0")
        ttk.Entry(settings_frame, textvariable=self.biz_km_var, width=15).grid(row=2, column=1, sticky="w", pady=4)

        self.round_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Round whole integer km only (No decimals)", variable=self.round_var).grid(row=2, column=2, columnspan=2, sticky="w", padx=(20, 0))

        # Middle section: Clients Table
        clients_frame = ttk.LabelFrame(main_frame, text=" 2. Client Destinations & Frequencies ", padding=12)
        clients_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Table & Scrollbar
        table_container = ttk.Frame(clients_frame)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        columns = ("name", "dist", "freq")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", height=8)
        self.tree.heading("name", text="Client / Destination Name")
        self.tree.heading("dist", text="One-way Distance (km)")
        self.tree.heading("freq", text="Frequency Category")

        self.tree.column("name", width=260)
        self.tree.column("dist", width=140, anchor="center")
        self.tree.column("freq", width=160, anchor="center")

        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons for tree view
        tree_btn_frame = ttk.Frame(clients_frame)
        tree_btn_frame.pack(fill=tk.X)

        ttk.Label(tree_btn_frame, text="Add New Destination:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_client_name = ttk.Entry(tree_btn_frame, width=20)
        self.new_client_name.insert(0, "")
        self.new_client_name.pack(side=tk.LEFT, padx=(0, 5))

        self.new_client_dist = ttk.Entry(tree_btn_frame, width=8)
        self.new_client_dist.insert(0, "")
        self.new_client_dist.pack(side=tk.LEFT, padx=(0, 5))

        self.new_client_freq = ttk.Combobox(tree_btn_frame, values=["Very Frequent", "Frequent", "Regular", "Occasional", "Rare"], width=13, state="readonly")
        self.new_client_freq.set("Frequent")
        self.new_client_freq.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(tree_btn_frame, text="➕ Add Client", command=self.add_client).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(tree_btn_frame, text="🗑️ Remove Selected", command=self.remove_client).pack(side=tk.RIGHT)

        # Bottom section: Actions
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X)

        ttk.Button(action_frame, text="📁 Load config.json", command=self.load_default_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="💾 Save config.json", command=self.save_config_to_file).pack(side=tk.LEFT)

        self.gen_btn = ttk.Button(action_frame, text="✨ Generate & Save Logbook Excel (.xlsx)", style="Accent.TButton", command=self.generate_logbook)
        self.gen_btn.pack(side=tk.RIGHT)

    def add_client(self):
        name = self.new_client_name.get().strip()
        dist_str = self.new_client_dist.get().strip()
        freq = self.new_client_freq.get()
        if not name:
            messagebox.showwarning("Input Error", "Please enter a destination name.")
            return
        try:
            dist = float(dist_str)
        except ValueError:
            messagebox.showwarning("Input Error", "Distance must be a valid number.")
            return

        self.tree.insert("", tk.END, values=(name, f"{dist:.1f}" if not dist.is_integer() else int(dist), freq))
        self.new_client_name.delete(0, tk.END)
        self.new_client_dist.delete(0, tk.END)

    def remove_client(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection", "Please select a row to remove.")
            return
        for item in selected:
            self.tree.delete(item)

    def load_default_config(self):
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if not os.path.exists(cfg_path):
            return
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.start_date_var.set(cfg.get("start_date", ""))
            self.end_date_var.set(cfg.get("end_date", ""))
            self.open_odo_var.set(str(cfg.get("opening_odo", 0)))
            self.close_odo_var.set(str(cfg.get("closing_odo", 0)))
            self.biz_km_var.set(str(cfg.get("target_business_km", 0)))
            self.round_var.set(cfg.get("round_numbers_only", True))

            for item in self.tree.get_children():
                self.tree.delete(item)

            for c in cfg.get("clients", []):
                dist = c["one_way_km"]
                dist_str = f"{dist:.1f}" if isinstance(dist, float) and not dist.is_integer() else str(int(dist))
                self.tree.insert("", tk.END, values=(c["name"], dist_str, c.get("frequency", "Frequent")))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load default config.json:\n{e}")

    def save_config_to_file(self):
        cfg = self.build_config_dict()
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=4)
            messagebox.showinfo("Saved", "Configuration saved to config.json successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config.json:\n{e}")

    def build_config_dict(self):
        clients = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            clients.append({
                "name": vals[0],
                "one_way_km": float(vals[1]) if '.' in str(vals[1]) else int(vals[1]),
                "frequency": vals[2]
            })

        # Preserve existing holidays/saturdays if config.json exists
        holidays, saturdays = [], []
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    old = json.load(f)
                holidays = old.get("holidays", [])
                saturdays = old.get("saturdays", [])
            except Exception:
                pass

        return {
            "start_date": self.start_date_var.get().strip(),
            "end_date": self.end_date_var.get().strip(),
            "opening_odo": int(self.open_odo_var.get().strip()),
            "closing_odo": int(self.close_odo_var.get().strip()),
            "target_business_km": int(self.biz_km_var.get().strip()),
            "round_numbers_only": self.round_var.get(),
            "holidays": holidays,
            "saturdays": saturdays,
            "clients": clients,
            "notes": ["Generated using Desktop GUI Tool"]
        }

    def generate_logbook(self):
        try:
            config = self.build_config_dict()
            if not config["clients"]:
                messagebox.showwarning("Warning", "Please add at least one client destination.")
                return

            save_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Spreadsheet", "*.xlsx")],
                title="Save Logbook As...",
                initialfile="Custom_Business_Travel_Logbook.xlsx"
            )
            if not save_path:
                return

            self.gen_btn.config(state="disabled", text="Generating...")
            self.update()

            engine = LogbookEngine(config)
            ledger, all_trips = engine.generate_trips()
            export_logbook_to_excel(config, ledger, all_trips, save_path)

            self.gen_btn.config(state="normal", text="✨ Generate & Save Logbook Excel (.xlsx)")

            msg = f"✅ Logbook successfully generated!\n\nSaved to: {save_path}\n\nWould you like to open the Excel spreadsheet now?"
            if messagebox.askyesno("Success!", msg):
                if os.name == 'nt':
                    os.startfile(save_path)
                else:
                    subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", save_path])

        except Exception as e:
            self.gen_btn.config(state="normal", text="✨ Generate & Save Logbook Excel (.xlsx)")
            messagebox.showerror("Error During Generation", f"An error occurred while generating the logbook:\n\n{e}")

if __name__ == "__main__":
    app = LogbookGUI()
    app.mainloop()
