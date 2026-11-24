# AetherStay AI — Integrated Hotel Management Expert System

A full-stack, rule-based **Hotel Management Expert System** built with Python (Flask), SQLite, and a Forward-Chaining Inference Engine with Certainty Factors and an Explanation Facility.

## System Architecture
1. **Knowledge Base (`knowledge_base.py`)**: Contains production rules (`IF-THEN`) across four operational domains:
   - Room Allocation & VIP Loyalty Upgrades (`R101`–`R105`)
   - Dynamic Yield & Revenue Pricing (`R201`–`R204`)
   - Housekeeping Turnaround & Eco-Programs (`R301`–`R302`)
   - Inventory Overbooking Risk Protection (`R401`)
   - Facility Maintenance Root-Cause Diagnostic Engine (HVAC, Plumbing, Electrical/RFID, IT)
2. **Inference Engine**: Priority-based conflict resolution with forward chaining and certainty factors (`CF`).
3. **Explanation Facility**: Generates human-readable reasoning traces showing why each rule fired.
4. **Integrated PMS Database (`database.py`)**: Persistent SQLite database (`data/hotel_expert.db`) tracking live rooms, reservations, housekeeping states, maintenance work orders, and audit logs.

## Windows Setup Instructions
1. Extract this ZIP archive to a folder (e.g., `C:\Hotel_Management_Expert_System`).
2. Double-click **`setup_and_run.bat`**.
3. The script will automatically create a virtual environment, install Flask, initialize the SQLite database, and open `http://127.0.0.1:5000` in your default web browser.
