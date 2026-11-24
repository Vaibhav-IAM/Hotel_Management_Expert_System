import json
import os
from datetime import datetime

class Rule:
    def __init__(self, rule_id, name, category, conditions, conclusions, priority=1, explanation_template=""):
        self.rule_id = rule_id
        self.name = name
        self.category = category
        self.conditions = conditions  # function(facts) -> (bool, certainty_factor)
        self.conclusions = conclusions  # dict of derived facts/recommendations
        self.priority = priority
        self.explanation_template = explanation_template


class HotelExpertSystem:
    """
    A comprehensive Rule-Based Expert System for Hotel Management featuring:
    1. Knowledge Base (Production Rules across Room Allocation, Dynamic Pricing,
       Housekeeping Scheduling, VIP & Loyalty Handling, and Maintenance Triage)
    2. Working Memory (Fact Base)
    3. Inference Engine (Forward Chaining with Certainty Factors & Conflict Resolution)
    4. Explanation Facility (Why/How reasoning trace for every triggered rule)
    """

    def __init__(self):
        self.rules = []
        self.trace = []
        self._build_knowledge_base()

    def _build_knowledge_base(self):
        # --- CATEGORY 1: ROOM ALLOCATION & UPGRADE RULES ---
        self.rules.append(Rule(
            rule_id="R101",
            name="Platinum VIP Complimentary Suite Upgrade",
            category="Room Allocation & VIP",
            priority=10,
            conditions=lambda f: (
                f.get("loyalty_tier") == "Platinum" and f.get("available_suites", 0) > 0 and f.get("requested_room") != "Presidential Suite",
                0.98
            ),
            conclusions={
                "recommended_room": "Executive Suite",
                "upgrade_applied": True,
                "discount_percent": 15,
                "welcome_amenity": "Complimentary Fruit Basket, Artisanal Chocolates & Late Checkout (4 PM)"
            },
            explanation_template="Guest holds Platinum loyalty status and Executive Suites are available; policy mandates complimentary tier upgrade and VIP welcome amenities."
        ))

        self.rules.append(Rule(
            rule_id="R102",
            name="Gold Member High-Floor Deluxe Priority",
            category="Room Allocation & VIP",
            priority=8,
            conditions=lambda f: (
                f.get("loyalty_tier") == "Gold" and f.get("available_deluxe", 0) > 0,
                0.92
            ),
            conclusions={
                "recommended_room": "Deluxe King (High Floor)",
                "upgrade_applied": f_or_true(True),
                "discount_percent": 10,
                "welcome_amenity": "Complimentary Welcome Drink & Express Check-In"
            },
            explanation_template="Guest holds Gold loyalty status; prioritized for high-floor Deluxe room with 10% loyalty discount."
        ))

        self.rules.append(Rule(
            rule_id="R103",
            name="Family & Group Connecting Rooms Rule",
            category="Room Allocation & VIP",
            priority=9,
            conditions=lambda f: (
                (f.get("adults", 1) + f.get("children", 0)) >= 4 or f.get("children", 0) >= 2,
                0.95
            ),
            conclusions={
                "recommended_room": "Family Suite / Interconnected Deluxe Rooms",
                "extra_bed_needed": True,
                "welcome_amenity": "Kids Activity Kit & Complimentary Breakfast for Children"
            },
            explanation_template="Party size is 4+ guests or includes 2+ children; system recommends interconnected rooms/Family Suite with extra bedding."
        ))

        self.rules.append(Rule(
            rule_id="R104",
            name="Corporate / Business Traveler Optimization",
            category="Room Allocation & VIP",
            priority=7,
            conditions=lambda f: (
                f.get("purpose") == "Business" and f.get("loyalty_tier") in ["Standard", "Silver"],
                0.88
            ),
            conclusions={
                "recommended_room": "Executive Business Room (Quiet Zone)",
                "discount_percent": 8,
                "welcome_amenity": "High-Speed Dedicated Wi-Fi, Ergonomic Workstation & Pressing of 2 Garments"
            },
            explanation_template="Guest is traveling on Business; allocated quiet-zone room with ergonomic desk and complimentary garment pressing."
        ))

        self.rules.append(Rule(
            rule_id="R105",
            name="Accessibility & Senior Citizen Ground/Elevator Proximity",
            category="Room Allocation & VIP",
            priority=10,
            conditions=lambda f: (
                f.get("special_needs") in ["Wheelchair Access", "Senior Citizen"],
                1.0
            ),
            conclusions={
                "accessibility_flag": "MANDATORY: Ground Floor or Immediate Elevator Proximity (ADA Compliant)",
                "priority_check_in": True
            },
            explanation_template="Guest indicated accessibility or senior citizen requirements; strict constraint enforced for ADA-compliant low-floor/elevator-adjacent room."
        ))

        # --- CATEGORY 2: DYNAMIC REVENUE & PRICING RULES ---
        self.rules.append(Rule(
            rule_id="R201",
            name="High Occupancy Surge Pricing",
            category="Dynamic Pricing",
            priority=9,
            conditions=lambda f: (
                f.get("occupancy_rate", 0) >= 85,
                0.95
            ),
            conclusions={
                "pricing_strategy": "Peak Demand Surge (+20%)",
                "rate_multiplier": 1.20
            },
            explanation_template="Current hotel occupancy is >= 85%; yield management rule triggers +20% peak demand rate adjustment."
        ))

        self.rules.append(Rule(
            rule_id="R202",
            name="Moderate Occupancy Standard Yield",
            category="Dynamic Pricing",
            priority=6,
            conditions=lambda f: (
                50 <= f.get("occupancy_rate", 0) < 85,
                0.90
            ),
            conclusions={
                "pricing_strategy": "Balanced Yield (Base Rate)",
                "rate_multiplier": 1.00
            },
            explanation_template="Hotel occupancy is between 50% and 84%; standard Best Available Rate (BAR) maintained."
        ))

        self.rules.append(Rule(
            rule_id="R203",
            name="Low Occupancy Promotional Stimulus",
            category="Dynamic Pricing",
            priority=8,
            conditions=lambda f: (
                f.get("occupancy_rate", 0) < 50,
                0.93
            ),
            conclusions={
                "pricing_strategy": "Low-Occupancy Stimulus (-15%)",
                "rate_multiplier": 0.85
            },
            explanation_template="Occupancy is below 50%; promotional 15% discount applied to stimulate room-night conversion."
        ))

        self.rules.append(Rule(
            rule_id="R204",
            name="Extended Stay Volume Discount",
            category="Dynamic Pricing",
            priority=7,
            conditions=lambda f: (
                f.get("nights", 1) >= 5,
                0.94
            ),
            conclusions={
                "extended_stay_bonus": "10% Long-Stay Rebate + Complimentary Airport Transfer"
            },
            explanation_template="Stay duration is 5 or more nights; long-stay incentive unlocked."
        ))

        # --- CATEGORY 3: HOUSEKEEPING & OPERATIONS RULES ---
        self.rules.append(Rule(
            rule_id="R301",
            name="Express Turnaround for Same-Day Check-In",
            category="Housekeeping & Ops",
            priority=10,
            conditions=lambda f: (
                f.get("early_checkin", False) or f.get("occupancy_rate", 0) >= 80,
                0.96
            ),
            conclusions={
                "housekeeping_priority": "URGENT (Red Tag - 30 Min Turnaround)",
                "staff_allocation": "Assign 2-person housekeeping team immediately"
            },
            explanation_template="Early check-in requested or occupancy >= 80%; room flagged for immediate 30-minute express turnaround."
        ))

        self.rules.append(Rule(
            rule_id="R302",
            name="Eco-Green Stay Linen Conservation",
            category="Housekeeping & Ops",
            priority=5,
            conditions=lambda f: (
                f.get("nights", 1) >= 3 and f.get("eco_preference", False),
                0.90
            ),
            conclusions={
                "housekeeping_priority": "Eco-Refresh (Towel/Linen change every 48h)",
                "eco_reward": "$10 F&B Dining Voucher awarded per night"
            },
            explanation_template="Guest opted into Eco-Green program on a 3+ night stay; full linen change scheduled every 48 hours with dining credit."
        ))

        # --- CATEGORY 4: OVERBOOKING & RISK MITIGATION ---
        self.rules.append(Rule(
            rule_id="R401",
            name="Critical Overbooking Protection Protocol",
            category="Risk & Inventory",
            priority=10,
            conditions=lambda f: (
                f.get("available_total", 10) <= 2,
                0.99
            ),
            conclusions={
                "inventory_alert": "CRITICAL: Close OTA channels immediately; hold remaining rooms for direct VIP arrivals."
            },
            explanation_template="Total available rooms dropped to 2 or fewer; automated channel manager freeze recommended to prevent walk-outs."
        ))

    def infer(self, initial_facts):
        """
        Executes Forward Chaining inference over the Knowledge Base.
        Returns derived conclusions, fired rules with certainty factors, and step-by-step reasoning trace.
        """
        working_memory = dict(initial_facts)
        fired_rules = []
        self.trace = []

        # Sort rules by priority descending (Conflict Resolution Strategy: Priority Ordering)
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            matched, cf = rule.conditions(working_memory)
            if matched:
                # Merge conclusions into working memory
                for k, v in rule.conclusions.items():
                    if k == "discount_percent" and k in working_memory:
                        working_memory[k] = max(working_memory[k], v)
                    else:
                        working_memory[k] = v

                fired_info = {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "category": rule.category,
                    "priority": rule.priority,
                    "certainty_factor": round(cf * 100, 1),
                    "conclusions": rule.conclusions,
                    "explanation": rule.explanation_template
                }
                fired_rules.append(fired_info)
                self.trace.append(f"[{rule.rule_id}] Fired '{rule.name}' (CF: {round(cf*100)}%) -> {rule.explanation_template}")

        # Calculate Final Recommended Rate
        base_rates = {
            "Standard Room": 120,
            "Deluxe King": 180,
            "Executive Business Room (Quiet Zone)": 210,
            "Deluxe King (High Floor)": 180,
            "Executive Suite": 320,
            "Family Suite / Interconnected Deluxe Rooms": 350,
            "Presidential Suite": 600
        }

        chosen_room = working_memory.get("recommended_room", working_memory.get("requested_room", "Standard Room"))
        base_price = base_rates.get(chosen_room, base_rates.get(working_memory.get("requested_room", "Standard Room"), 150))
        multiplier = working_memory.get("rate_multiplier", 1.0)
        discount = working_memory.get("discount_percent", 0)
        nights = max(1, int(working_memory.get("nights", 1)))

        nightly_rate = round(base_price * multiplier * (1 - discount / 100.0), 2)
        total_estimate = round(nightly_rate * nights, 2)

        working_memory["final_room_assigned"] = chosen_room
        working_memory["base_nightly_rate"] = base_price
        working_memory["final_nightly_rate"] = nightly_rate
        working_memory["total_stay_estimate"] = total_estimate

        return {
            "working_memory": working_memory,
            "fired_rules": fired_rules,
            "reasoning_trace": self.trace,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def diagnose_maintenance(self, symptom_data):
        """
        Diagnostic Sub-System (Backward-style Symptom Triage for Hotel Facilities)
        """
        category = symptom_data.get("system", "HVAC")
        symptom = symptom_data.get("symptom", "")
        severity = symptom_data.get("severity", "Medium")
        room_occupied = symptom_data.get("occupied", False)

        diagnosis = {
            "fault_classification": "General Maintenance",
            "root_cause_hypothesis": "Component wear or sensor calibration drift.",
            "action_plan": ["Dispatch duty technician within 2 hours."],
            "sla_minutes": 120,
            "guest_relocation_required": False,
            "confidence": 85
        }

        if category == "HVAC":
            if "No Cooling" in symptom or "Warm Air" in symptom:
                diagnosis = {
                    "fault_classification": "Chiller Valve / Refrigerant / Thermostat Failure",
                    "root_cause_hypothesis": "Actuator valve stuck closed or low refrigerant pressure in Fan Coil Unit (FCU).",
                    "action_plan": [
                        "1. Reset digital thermostat & check breaker panel.",
                        "2. Inspect FCU chilled water actuator valve.",
                        "3. Offer immediate room move if guest is in-house and outside temp > 28°C."
                    ],
                    "sla_minutes": 20 if room_occupied else 60,
                    "guest_relocation_required": room_occupied,
                    "confidence": 94
                }
            elif "Water Leak" in symptom:
                diagnosis = {
                    "fault_classification": "Blocked Condensate Drain Pan",
                    "root_cause_hypothesis": "Algae/debris blockage in FCU condensate drain line causing overflow.",
                    "action_plan": [
                        "1. Shut off FCU immediately to prevent ceiling/carpet water damage.",
                        "2. Vacuum flush condensate drain line.",
                        "3. Relocate guest immediately if occupied."
                    ],
                    "sla_minutes": 15,
                    "guest_relocation_required": room_occupied,
                    "confidence": 97
                }
        elif category == "Plumbing":
            if "No Hot Water" in symptom:
                diagnosis = {
                    "fault_classification": "Recirculation Pump / Mixing Valve Fault",
                    "root_cause_hypothesis": "Thermostatic mixing valve failure or floor riser air-lock.",
                    "action_plan": [
                        "1. Check floor hot-water return loop temperature.",
                        "2. Purge air from riser or recalibrate mixing valve.",
                        "3. Provide complimentary spa shower access if repair > 30 mins."
                    ],
                    "sla_minutes": 25 if room_occupied else 90,
                    "guest_relocation_required": False,
                    "confidence": 91
                }
            elif "Leak" in symptom or "Overflow" in symptom:
                diagnosis = {
                    "fault_classification": "Critical Water Ingress Hazard",
                    "root_cause_hypothesis": "Pressurized supply line joint failure or flush valve seal rupture.",
                    "action_plan": [
                        "1. Isolate room shut-off valve immediately.",
                        "2. Deploy wet-vac & dehumidifier.",
                        "3. Mandatory immediate room relocation + complimentary dinner voucher."
                    ],
                    "sla_minutes": 10,
                    "guest_relocation_required": True,
                    "confidence": 98
                }
        elif category == "Electrical / Smart Lock":
            if "Smart Lock" in symptom or "Keycard" in symptom:
                diagnosis = {
                    "fault_classification": "RFID Reader Battery / Encoder Sync Error",
                    "root_cause_hypothesis": "Low battery voltage on mortise lock or PMS encoder clock drift.",
                    "action_plan": [
                        "1. Escort guest with physical master override key within 5 minutes.",
                        "2. Connect handheld programmer to read lock audit trail & replace battery pack."
                    ],
                    "sla_minutes": 5,
                    "guest_relocation_required": False,
                    "confidence": 96
                }
            elif "Power Outage" in symptom:
                diagnosis = {
                    "fault_classification": "Tripped RCBO / Keycard Energy Saver Switch Fault",
                    "root_cause_hypothesis": "Guest appliance overload tripped room distribution board or wall energy-saver relay failed.",
                    "action_plan": [
                        "1. Inspect room DB panel and reset tripped breaker.",
                        "2. Test wall keycard power slot relay."
                    ],
                    "sla_minutes": 15,
                    "guest_relocation_required": False,
                    "confidence": 93
                }
        elif category == "IT / Wi-Fi":
            diagnosis = {
                "fault_classification": "Access Point Drop / VLAN Auth Timeout",
                "root_cause_hypothesis": "In-room wall AP PoE drop or captive portal DHCP lease exhaustion.",
                "action_plan": [
                    "1. Power-cycle PoE port on floor switch for room AP.",
                    "2. Whitelist guest MAC address directly on gateway."
                ],
                "sla_minutes": 20,
                "guest_relocation_required": False,
                "confidence": 92
            }

        return diagnosis


def f_or_true(val):
    return val
