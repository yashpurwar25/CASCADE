"""
mock_data.py
Seed data for the CASCADE demo: vendors, BOM, project schedule.
This stands in for what would normally come from a Kojo/ERP connector.
"""

from datetime import date

# --- Vendors -----------------------------------------------------------
VENDORS = {
    "GlobalSteel_Co": {
        "reliability_score": 0.71,
        "region": "Long Beach Port",
        "avg_lead_time_days": 24,
        "multi_warehouse": True,
    },
    "Local_Supplier_X": {
        "reliability_score": 0.93,
        "region": "Regional (Inland)",
        "avg_lead_time_days": 9,
        "multi_warehouse": False,
    },
    "HVAC_Partners_Inc": {
        "reliability_score": 0.85,
        "region": "Gulf Coast",
        "avg_lead_time_days": 18,
        "multi_warehouse": True,
    },
}

# --- Bill of Materials ---------------------------------------------------
BOM = [
    {
        "item": "Structural Steel",
        "vendor": "GlobalSteel_Co",
        "origin_region": "Long Beach Port",
        "promised_date": date(2026, 10, 12),
        "qty": 1,
        "unit_cost": 180000,
    },
    {
        "item": "HVAC Units",
        "vendor": "HVAC_Partners_Inc",
        "origin_region": "Gulf Coast",
        "promised_date": date(2026, 10, 20),
        "qty": 1,
        "unit_cost": 95000,
    },
]

# --- Project schedule (simplified CPM network) ---------------------------
# Each activity: duration in days, and which activities depend on it.
SCHEDULE = {
    "Steel Delivery":     {"duration": 0,  "depends_on": [],
                            "float_days": 0, "crew": None},
    "Steel Erection":     {"duration": 10, "depends_on": ["Steel Delivery"],
                            "float_days": 0, "crew": "Structural Crew A"},
    "HVAC Install":       {"duration": 7,  "depends_on": ["Steel Erection"],
                            "float_days": 2, "crew": "HVAC Crew A"},
    "Drywall":            {"duration": 5,  "depends_on": ["HVAC Install"],
                            "float_days": 2, "crew": "Finishing Crew"},
    "Final Handover":     {"duration": 1,  "depends_on": ["Drywall"],
                            "float_days": 0, "crew": None},
}

# --- Causal knowledge graph: (subject, predicate, object) triplets -------
KNOWLEDGE_GRAPH = [
    ("Structural Steel", "depends_on", "Long Beach Port"),
    ("Long Beach Port", "status", "Normal"),
    ("Structural Steel", "has_alternate", "Local_Supplier_X"),
    ("Local_Supplier_X", "reliability", "0.93"),
    ("HVAC Units", "depends_on", "Gulf Coast Shipping"),
    ("Gulf Coast Shipping", "status", "Normal"),
    ("HVAC Units", "has_alternate", "HVAC_Partners_Inc_Backup"),
]

# --- Chaos Menu scenarios -------------------------------------------------
CHAOS_SCENARIOS = {
    "A) Port Strike — Long Beach": {
        "affected_region": "Long Beach Port",
        "affected_item": "Structural Steel",
        "headline": "Dockworkers union strikes at Port of Long Beach",
    },
    "B) Hurricane — Gulf Coast": {
        "affected_region": "Gulf Coast",
        "affected_item": "HVAC Units",
        "headline": "Category 3 hurricane makes landfall near Gulf shipping lanes",
    },
    "C) Vendor Bankruptcy": {
        "affected_region": None,
        "affected_item": "Structural Steel",
        "headline": "GlobalSteel_Co files for Chapter 11 bankruptcy protection",
    },
}