from flask import Flask, render_template, request, jsonify
from datetime import datetime
import random
import json
from database import init_db, get_connection
from knowledge_base import HotelExpertSystem

app = Flask(__name__)
expert_engine = HotelExpertSystem()

# Initialize SQLite Database on startup
init_db()


def get_hotel_metrics():
    conn = get_connection()
    rooms = conn.execute("SELECT * FROM rooms ORDER BY room_number").fetchall()
    bookings = conn.execute("SELECT * FROM bookings ORDER BY id DESC").fetchall()
    tickets = conn.execute("SELECT * FROM maintenance_tickets ORDER BY id DESC").fetchall()
    logs = conn.execute("SELECT * FROM expert_logs ORDER BY id DESC LIMIT 15").fetchall()
    conn.close()

    total_rooms = len(rooms)
    occupied_rooms = sum(1 for r in rooms if r["status"] == "Occupied")
    available_rooms = sum(1 for r in rooms if r["status"] == "Available")
    maintenance_rooms = sum(1 for r in rooms if r["status"] == "Maintenance")
    dirty_rooms = sum(1 for r in rooms if r["housekeeping_status"] == "Dirty")

    occupancy_rate = round((occupied_rooms / total_rooms) * 100, 1) if total_rooms > 0 else 0
    active_revenue = sum(b["total_amount"] for b in bookings if b["status"] == "Checked-In")

    avail_suites = sum(1 for r in rooms if r["status"] == "Available" and "Suite" in r["room_type"])
    avail_deluxe = sum(1 for r in rooms if r["status"] == "Available" and "Deluxe" in r["room_type"])

    return {
        "rooms": [dict(r) for r in rooms],
        "bookings": [dict(b) for b in bookings],
        "tickets": [dict(t) for t in tickets],
        "logs": [dict(l) for l in logs],
        "stats": {
            "total_rooms": total_rooms,
            "occupied_rooms": occupied_rooms,
            "available_rooms": available_rooms,
            "maintenance_rooms": maintenance_rooms,
            "dirty_rooms": dirty_rooms,
            "occupancy_rate": occupancy_rate,
            "active_revenue": round(active_revenue, 2),
            "avail_suites": avail_suites,
            "avail_deluxe": avail_deluxe
        }
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state", methods=["GET"])
def api_state():
    return jsonify(get_hotel_metrics())


@app.route("/api/expert/consult", methods=["POST"])
def expert_consult():
    data = request.json
    metrics = get_hotel_metrics()
    stats = metrics["stats"]

    facts = {
        "guest_name": data.get("guest_name", "Walk-in Guest"),
        "loyalty_tier": data.get("loyalty_tier", "Standard"),
        "purpose": data.get("purpose", "Leisure"),
        "requested_room": data.get("requested_room", "Standard Room"),
        "adults": int(data.get("adults", 1)),
        "children": int(data.get("children", 0)),
        "nights": int(data.get("nights", 1)),
        "special_needs": data.get("special_needs", "None"),
        "early_checkin": bool(data.get("early_checkin", False)),
        "eco_preference": bool(data.get("eco_preference", False)),
        "occupancy_rate": stats["occupancy_rate"],
        "available_total": stats["available_rooms"],
        "available_suites": stats["avail_suites"],
        "available_deluxe": stats["avail_deluxe"]
    }

    result = expert_engine.infer(facts)

    # Log inference to database
    conn = get_connection()
    fired_ids = ", ".join([r["rule_id"] for r in result["fired_rules"]]) or "None (Base Policy)"
    conn.execute("""
        INSERT INTO expert_logs (action_type, input_summary, rules_fired, recommendation, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "Reservation & Yield Inference",
        f"{facts['guest_name']} ({facts['loyalty_tier']}, {facts['nights']}N, Occ: {stats['occupancy_rate']}%)",
        fired_ids,
        f"Assigned: {result['working_memory']['final_room_assigned']} @ ${result['working_memory']['final_nightly_rate']}/night",
        result["timestamp"]
    ))
    conn.commit()
    conn.close()

    return jsonify(result)


@app.route("/api/bookings/create", methods=["POST"])
def create_booking():
    data = request.json
    conn = get_connection()

    room_type = data.get("room_type", "Standard Room")
    # Find best matching available room
    room = conn.execute(
        "SELECT * FROM rooms WHERE status = 'Available' AND room_type LIKE ? ORDER BY floor DESC LIMIT 1",
        (f"%{room_type.split(' (')[0]}%",)
    ).fetchone()

    if not room:
        # Fallback to any available room
        room = conn.execute("SELECT * FROM rooms WHERE status = 'Available' LIMIT 1").fetchone()

    if not room:
        conn.close()
        return jsonify({"success": False, "error": "No available rooms in inventory!"}), 400

    booking_ref = f"BK-{random.randint(2000, 9999)}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nights = max(1, int(data.get("nights", 1)))
    nightly_rate = float(data.get("nightly_rate", room["base_rate"]))
    total_amount = round(nightly_rate * nights, 2)

    conn.execute("""
        INSERT INTO bookings (booking_ref, guest_name, guest_email, loyalty_tier, purpose, adults, children, nights, room_number, room_type, nightly_rate, total_amount, status, ai_notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Checked-In', ?, ?)
    """, (
        booking_ref,
        data.get("guest_name", "Guest"),
        data.get("guest_email", ""),
        data.get("loyalty_tier", "Standard"),
        data.get("purpose", "Leisure"),
        int(data.get("adults", 1)),
        int(data.get("children", 0)),
        nights,
        room["room_number"],
        room["room_type"],
        nightly_rate,
        total_amount,
        data.get("ai_notes", "Expert System Assisted Booking"),
        now
    ))

    conn.execute("UPDATE rooms SET status = 'Occupied', housekeeping_status = 'Occupied' WHERE room_number = ?", (room["room_number"],))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "booking_ref": booking_ref, "room_number": room["room_number"]})


@app.route("/api/bookings/checkout/<int:booking_id>", methods=["POST"])
def checkout_booking(booking_id):
    conn = get_connection()
    booking = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if not booking:
        conn.close()
        return jsonify({"success": False, "error": "Booking not found"}), 404

    conn.execute("UPDATE bookings SET status = 'Checked-Out' WHERE id = ?", (booking_id,))
    conn.execute("UPDATE rooms SET status = 'Available', housekeeping_status = 'Dirty' WHERE room_number = ?", (booking["room_number"],))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/rooms/housekeeping/<room_number>", methods=["POST"])
def toggle_housekeeping(room_number):
    conn = get_connection()
    room = conn.execute("SELECT * FROM rooms WHERE room_number = ?", (room_number,)).fetchone()
    if not room:
        conn.close()
        return jsonify({"success": False, "error": "Room not found"}), 404

    new_hk = "Clean" if room["housekeeping_status"] != "Clean" else "Dirty"
    conn.execute("UPDATE rooms SET housekeeping_status = ? WHERE room_number = ?", (new_hk, room_number))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "new_status": new_hk})


@app.route("/api/maintenance/diagnose", methods=["POST"])
def diagnose_maintenance():
    data = request.json
    room_number = data.get("room_number", "101")
    conn = get_connection()
    room = conn.execute("SELECT * FROM rooms WHERE room_number = ?", (room_number,)).fetchone()
    occupied = (room["status"] == "Occupied") if room else False

    symptom_input = {
        "system": data.get("system", "HVAC"),
        "symptom": data.get("symptom", ""),
        "severity": data.get("severity", "Medium"),
        "occupied": occupied
    }

    diagnosis = expert_engine.diagnose_maintenance(symptom_input)

    if data.get("create_ticket", False):
        ticket_ref = f"MNT-{random.randint(1000, 9999)}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            INSERT INTO maintenance_tickets (ticket_ref, room_number, system_category, symptom, diagnosis, action_plan, sla_minutes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Open', ?)
        """, (
            ticket_ref,
            room_number,
            symptom_input["system"],
            symptom_input["symptom"],
            diagnosis["fault_classification"],
            " | ".join(diagnosis["action_plan"]),
            diagnosis["sla_minutes"],
            now
        ))
        if diagnosis["guest_relocation_required"] or not occupied:
            conn.execute("UPDATE rooms SET status = 'Maintenance' WHERE room_number = ?", (room_number,))

        conn.execute("""
            INSERT INTO expert_logs (action_type, input_summary, rules_fired, recommendation, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Maintenance Diagnostic Triage",
            f"Room {room_number} - {symptom_input['system']}: {symptom_input['symptom']}",
            f"Diagnostic Tree (Conf: {diagnosis['confidence']}%)",
            f"{diagnosis['fault_classification']} (SLA: {diagnosis['sla_minutes']}m)",
            now
        ))
        conn.commit()

    conn.close()
    return jsonify({"diagnosis": diagnosis, "room_occupied": occupied})


@app.route("/api/maintenance/resolve/<int:ticket_id>", methods=["POST"])
def resolve_ticket(ticket_id):
    conn = get_connection()
    ticket = conn.execute("SELECT * FROM maintenance_tickets WHERE id = ?", (ticket_id,)).fetchone()
    if ticket:
        conn.execute("UPDATE maintenance_tickets SET status = 'Resolved' WHERE id = ?", (ticket_id,))
        conn.execute("UPDATE rooms SET status = 'Available', housekeeping_status = 'Clean' WHERE room_number = ? AND status = 'Maintenance'", (ticket["room_number"],))
        conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/rules", methods=["GET"])
def get_rules():
    rules_list = [
        {
            "rule_id": r.rule_id,
            "name": r.name,
            "category": r.category,
            "priority": r.priority,
            "explanation": r.explanation_template
        }
        for r in expert_engine.rules
    ]
    return jsonify({"rules": rules_list})


if __name__ == "__main__":
    print("====================================================")
    print("  Hotel Management Expert System (AI-PMS) Running   ")
    print("  Access Dashboard at: http://127.0.0.1:5000        ")
    print("====================================================")
    app.run(host="127.0.0.1", port=5000, debug=True)
