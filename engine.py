"""
engine.py
The "brain" of CASCADE: forecast, CPM impact, knowledge-graph traversal,
and a simulated ReAct trace. Lightweight stand-ins for the real
quantile-regression / CPM-solver / causal-DAG math described in the doc —
same interfaces, so swapping in real models later doesn't change the UI.
"""

import random
from datetime import timedelta
from mock_data import BOM, SCHEDULE, KNOWLEDGE_GRAPH, VENDORS


# ---------------------------------------------------------------------
# Pillar 1: Probabilistic Lead-Time Forecasting (quantile regression stand-in)
# ---------------------------------------------------------------------
def forecast_delay(item_name: str, disrupted: bool):
    """Returns 10th/50th/90th percentile delivery shift in days."""
    bom_entry = next(b for b in BOM if b["item"] == item_name)
    vendor = VENDORS[bom_entry["vendor"]]
    base_reliability = vendor["reliability_score"]

    if not disrupted:
        p10, p50, p90 = 0, 1, 3
    else:
        severity = round((1 - base_reliability) * 10) + random.randint(6, 10)
        p10 = max(1, severity - 4)
        p50 = severity
        p90 = severity + 8

    return {
        "item": item_name,
        "p10_days": p10,
        "p50_days": p50,
        "p90_days": p90,
        "promised_date": bom_entry["promised_date"],
        "p10_date": bom_entry["promised_date"] + timedelta(days=p10),
        "p50_date": bom_entry["promised_date"] + timedelta(days=p50),
        "p90_date": bom_entry["promised_date"] + timedelta(days=p90),
        "coverage_error_pct": 10,
    }


# ---------------------------------------------------------------------
# Pillar 2: Critical Path + Resource (RCPSP-lite) impact
# ---------------------------------------------------------------------
def calculate_cascade_impact(delay_days: int):
    """
    Very small forward-pass CPM: a delay on Steel Delivery pushes every
    downstream activity that has zero float by the same number of days.
    Returns the affected activities and whether it hits the critical path.
    """
    affected = []
    total_push = 0
    for name, info in SCHEDULE.items():
        if name == "Steel Delivery":
            continue
        if info["float_days"] == 0:
            total_push = delay_days
            affected.append({"activity": name, "crew": info["crew"],
                              "pushed_days": delay_days})
        elif delay_days > info["float_days"]:
            overrun = delay_days - info["float_days"]
            affected.append({"activity": name, "crew": info["crew"],
                              "pushed_days": overrun})

    handover_push = delay_days  # zero float all the way to handover in this mini-network
    idle_crew_days = sum(SCHEDULE[a["activity"]]["duration"] for a in affected
                          if a["activity"] in ("HVAC Install", "Drywall"))

    return {
        "critical_path_hit": True,
        "handover_push_days": handover_push,
        "affected_activities": affected,
        "idle_crew_days": idle_crew_days,
    }


# ---------------------------------------------------------------------
# Pillar 3: Causal knowledge graph traversal
# ---------------------------------------------------------------------
def traverse_knowledge_graph(item_name: str, disrupted_region: str | None):
    """Walks KNOWLEDGE_GRAPH triplets to find an alternate supplier + reasoning path."""
    path = []
    alternate = None

    for s, p, o in KNOWLEDGE_GRAPH:
        if s == item_name and p == "depends_on":
            path.append(f"{item_name} --depends_on--> {o}")
            if disrupted_region and o == disrupted_region:
                path.append(f"{o} --status--> STRUCK")
        if s == item_name and p == "has_alternate":
            alternate = o
            path.append(f"{item_name} --has_alternate--> {o}")

    confidence = random.choice([68, 72, 75, 81])
    evidence_notes = f"Based on 3 industry benchmarks and 1 current news signal, " \
                      f"probability of this fix resolving the delay is {confidence}%."

    return {
        "path": path,
        "recommended_alternate": alternate,
        "confidence_pct": confidence,
        "evidence_notes": evidence_notes,
    }


# ---------------------------------------------------------------------
# Pillar 4: ReAct agent trace (Thought -> Action -> Observation)
# ---------------------------------------------------------------------
def generate_react_trace(scenario_headline: str, affected_item: str, affected_region):
    trace = [
        ("Thought", f"I see a signal in the news feed: \"{scenario_headline}\". "
                     "I need to check the BOM for items sourced from that region."),
        ("Action", f"get_bom_items(origin=\"{affected_region}\")"),
        ("Observation", f"\"{affected_item}\" is affected."),
        ("Thought", "Now I calculate the blast radius and query the knowledge graph for alternatives."),
        ("Action", f"query_knowledge_graph(item=\"{affected_item}\")"),
        ("Observation", "Alternate supplier found with higher reliability score."),
        ("Thought", "I'll draft a recommendation for PM approval rather than acting directly."),
        ("Action", "draft_procurement_email(vendor=recommended_alternate)"),
        ("Observation", "Draft created. Routed to approval queue. Not sent."),
    ]
    return trace


# ---------------------------------------------------------------------
# Financial impact: Days into dollars
# ---------------------------------------------------------------------
def calculate_financial_impact(idle_crew_days: int, crew_size: int = 10,
                                daily_rate: int = 240, material_cost_delta_pct: float = 5.0,
                                base_material_cost: int = 180000):
    idle_cost = idle_crew_days * crew_size * daily_rate
    material_delta = base_material_cost * (material_cost_delta_pct / 100)
    net_savings = idle_cost - material_delta
    return {
        "idle_cost": idle_cost,
        "material_delta": material_delta,
        "net_savings": max(net_savings, 0),
    }