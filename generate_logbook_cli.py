#!/usr/bin/env python3
"""
Interactive or Config-driven CLI for Business Travel Logbook Generator
Run: python generate_logbook_cli.py [--config config.json] [--output my_logbook.xlsx]
"""

import sys
import os
import json
import argparse
from logbook_engine import LogbookEngine
from export_excel import export_logbook_to_excel

def interactive_prompt():
    print("=========================================================")
    print("       BUSINESS TRAVEL LOGBOOK GENERATOR (CLI)          ")
    print("=========================================================")
    print("Answer the prompts below to generate your custom logbook.\n")

    start_date = input("Start Date (YYYY-MM-DD): ").strip()
    while not start_date:
        start_date = input("Start Date (YYYY-MM-DD) is required: ").strip()

    end_date = input("End Date (YYYY-MM-DD): ").strip()
    while not end_date:
        end_date = input("End Date (YYYY-MM-DD) is required: ").strip()

    open_odo_str = input("Opening Odometer (km): ").strip()
    opening_odo = int(open_odo_str) if open_odo_str.isdigit() else 0

    close_odo_str = input("Closing Odometer (km): ").strip()
    closing_odo = int(close_odo_str) if close_odo_str.isdigit() else 0

    biz_km_str = input("Total Business km target: ").strip()
    target_business_km = int(biz_km_str) if biz_km_str.isdigit() else 0

    round_opt = input("Use rounded whole integer km only (No decimals)? (y/n) [default: y]: ").strip().lower()
    round_numbers_only = (round_opt != 'n')

    print("\n--- Clients / Destinations ---")
    print("Enter your clients one by one. Press ENTER on Client Name when done.")
    clients = []
    while True:
        c_name = input(f"\nClient #{len(clients)+1} Name (or ENTER to finish): ").strip()
        if not c_name:
            if not clients:
                print("⚠️ Please enter at least one client destination.")
                continue
            break
        
        c_dist_str = input(f"One-way distance to {c_name} (km): ").strip()
        try:
            c_dist = float(c_dist_str) if not round_numbers_only else int(round(float(c_dist_str)))
        except ValueError:
            c_dist = 10

        print("Frequencies: 1=Very Frequent, 2=Frequent, 3=Regular, 4=Occasional, 5=Rare")
        f_opt = input("Select frequency (1-5) [default: 2]: ").strip() or "2"
        f_map = {"1": "Very Frequent", "2": "Frequent", "3": "Regular", "4": "Occasional", "5": "Rare"}
        c_freq = f_map.get(f_opt, "Frequent")

        clients.append({
            "name": c_name,
            "one_way_km": c_dist,
            "frequency": c_freq
        })

    config = {
        "start_date": start_date,
        "end_date": end_date,
        "opening_odo": opening_odo,
        "closing_odo": closing_odo,
        "target_business_km": target_business_km,
        "round_numbers_only": round_numbers_only,
        "holidays": [],
        "saturdays": [],
        "clients": clients,
        "notes": ["Generated using Interactive CLI"]
    }

    return config

def main():
    parser = argparse.ArgumentParser(description="Generate Business Travel Logbook Excel Spreadsheet")
    parser.add_argument("--config", "-c", help="Path to config JSON file (if omitted, starts interactive prompt or uses config.json)")
    parser.add_argument("--output", "-o", default="Generated_Logbook.xlsx", help="Output Excel filename")
    parser.add_argument("--interactive", "-i", action="store_true", help="Force interactive prompts")

    args = parser.parse_args()

    if args.interactive or (not args.config and not os.path.exists("config.json")):
        config = interactive_prompt()
    else:
        cfg_path = args.config or "config.json"
        print(f"Loading configuration from: {cfg_path}")
        with open(cfg_path, "r", encoding="utf-8") as f:
            config = json.load(f)

    print("\nProcessing trips and computing odometer ledger...")
    engine = LogbookEngine(config)
    ledger, all_trips = engine.generate_trips()

    out_path = os.path.abspath(args.output)
    print(f"Exporting to Excel: {out_path}")
    export_logbook_to_excel(config, ledger, all_trips, out_path)
    print(f"✅ Logbook successfully generated! Saved to:\n   {out_path}\n")

if __name__ == "__main__":
    main()
