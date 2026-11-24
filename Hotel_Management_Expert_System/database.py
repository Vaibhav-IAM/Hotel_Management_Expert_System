import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "hotel_expert.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    # Rooms Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            floor INTEGER NOT NULL,
            base_rate REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Available',
            housekeeping_status TEXT NOT NULL DEFAULT 'Clean',
            features TEXT
        )
    """)

    # Reservations / Bookings Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_ref TEXT UNIQUE NOT NULL,
            guest_name TEXT NOT NULL,
            guest_email TEXT,
            loyalty_tier TEXT NOT NULL,
            purpose TEXT NOT NULL,
            adults INTEGER NOT NULL,
            children INTEGER NOT NULL,
            nights INTEGER NOT NULL,
            room_number TEXT NOT NULL,
            room_type TEXT NOT NULL,
            nightly_rate REAL NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Checked-In',
            ai_notes TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Maintenance Tickets Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_ref TEXT UNIQUE NOT NULL,
            room_number TEXT NOT NULL,
            system_category TEXT NOT NULL,
            symptom TEXT NOT NULL,
            diagnosis TEXT NOT NULL,
            action_plan TEXT NOT NULL,
            sla_minutes INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT NOT NULL
        )
    """)

    # Audit Log of Expert System Decisions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expert_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            input_summary TEXT NOT NULL,
            rules_fired TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Seed initial rooms if empty
    cur.execute("SELECT COUNT(*) as cnt FROM rooms")
    if cur.fetchone()["cnt"] == 0:
        sample_rooms = [
            ("101", "Standard Room", 1, 120.0, "Available", "Clean", "ADA Accessible, Garden View"),
            ("102", "Standard Room", 1, 120.0, "Occupied", "Occupied", "Twin Beds, Courtyard"),
            ("103", "Standard Room", 1, 120.0, "Available", "Clean", "Queen Bed, Quiet Wing"),
            ("104", "Deluxe King", 1, 180.0, "Available", "Dirty", "King Bed, Patio Access"),
            ("201", "Deluxe King", 2, 180.0, "Occupied", "Occupied", "King Bed, City View"),
            ("202", "Deluxe King", 2, 180.0, "Available", "Clean", "King Bed, High-Speed Desk"),
            ("203", "Deluxe King", 2, 180.0, "Available", "Clean", "Interconnecting Option"),
            ("204", "Executive Business Room (Quiet Zone)", 2, 210.0, "Available", "Clean", "Ergonomic Chair, Dual Monitor Dock"),
            ("301", "Executive Suite", 3, 320.0, "Available", "Clean", "Separate Living Area, Panoramic View"),
            ("302", "Executive Suite", 3, 320.0, "Occupied", "Occupied", "Corner Suite, Jacuzzi"),
            ("303", "Family Suite / Interconnected Deluxe Rooms", 3, 350.0, "Available", "Clean", "2 Bedrooms, Kids Zone"),
            ("401", "Presidential Suite", 4, 600.0, "Available", "Clean", "Private Terrace, Butler Service, Dining Room")
        ]
        cur.executemany("""
            INSERT INTO rooms (room_number, room_type, floor, base_rate, status, housekeeping_status, features)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_rooms)

    # Seed sample bookings if empty
    cur.execute("SELECT COUNT(*) as cnt FROM bookings")
    if cur.fetchone()["cnt"] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sample_bookings = [
            ("BK-1001", "Aarav Sharma", "aarav.sharma@example.com", "Platinum", "Business", 1, 0, 3, "302", "Executive Suite", 272.0, 816.0, "Checked-In", "R101 Platinum Upgrade + R202 Balanced Yield", now),
            ("BK-1002", "Priya Nair", "priya.nair@example.com", "Gold", "Leisure", 2, 1, 2, "201", "Deluxe King", 162.0, 324.0, "Checked-In", "R102 Gold Priority + 10% Discount", now),
            ("BK-1003", "Rohan Verma", "rohan.v@example.com", "Standard", "Leisure", 2, 0, 1, "102", "Standard Room", 120.0, 120.0, "Checked-In", "Standard BAR Rate", now)
        ]
        cur.executemany("""
            INSERT INTO bookings (booking_ref, guest_name, guest_email, loyalty_tier, purpose, adults, children, nights, room_number, room_type, nightly_rate, total_amount, status, ai_notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_bookings)

    conn.commit()
    conn.close()
