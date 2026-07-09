"""
app.py
CASCADE War Room — Streamlit demo UI.
Run with: streamlit run app.py
"""

import os
import time
import streamlit as st
import plotly.graph_objects as go

from mock_data import CHAOS_SCENARIOS, VENDORS, SCHEDULE
from engine import (
    forecast_delay,
    calculate_cascade_impact,
    traverse_knowledge_graph,
    generate_react_trace,
    calculate_financial_impact,
    reject_and_find_alternate,
    get_pareto_options,
    get_portfolio_impact,
    run_cpm,
)

# Live ReAct trace is optional — only used if ANTHROPIC_API_KEY is set
try:
    from engine import generate_react_trace_live
    LIVE_AGENT_AVAILABLE = bool(os.environ.get("ANTHROPIC_API_KEY"))
except ImportError:
    LIVE_AGENT_AVAILABLE = False

st.set_page_config(page_title="CASCADE — War Room", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------
# Dark "command center" theme
# ---------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0a0e14; color: #e0e6ed; }
    h1, h2, h3 { color: #e0e6ed !important; }
    .loss-clock {
        font-size: 52px; font-weight: 800; color: #ff4b4b;
        text-align: center; font-family: 'Courier New', monospace;
    }
    .loss-clock-label { text-align: center; color: #8b949e; font-size: 14px; letter-spacing: 2px; }
    .panel {
        background-color: #11161f; border: 1px solid #21262d;
        border-radius: 8px; padding: 16px; margin-bottom: 12px;
    }
    .trace-line { font-family: 'Courier New', monospace; font-size: 13px; margin-bottom: 4px; }
    .thought { color: #58a6ff; }
    .action { color: #f2cc60; }
    .observation { color: #3fb950; }
    .legacy-box {
        background-color: #1a1a1a; border: 1px dashed #444; border-radius: 8px;
        padding: 20px; color: #999; font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------
if "scenario_run" not in st.session_state:
    st.session_state.scenario_run = False
    st.session_state.scenario_name = None
    st.session_state.loss_value = 0
    st.session_state.resolved = False
if "rejection_alt" not in st.session_state:
    st.session_state.rejection_alt = None

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
st.title("🛡 CASCADE — Cognitive Supply Chain Resilience Engine")
st.caption("From reactive tracking to proactive, agentic intelligence.")
if LIVE_AGENT_AVAILABLE:
    st.caption("🟢 Live agent connected — ReAct trace is generated in real time by Claude.")
else:
    st.caption("🟡 Running in scripted-trace mode (set ANTHROPIC_API_KEY for a live agent).")

# ---------------------------------------------------------------------
# Legacy vs CASCADE split screen (top)
# ---------------------------------------------------------------------
col_legacy, col_cascade = st.columns(2)
with col_legacy:
    st.markdown("#### The Legacy Way")
    st.markdown("""
    <div class="legacy-box">
    📊 static_delivery_log.xlsx<br><br>
    📞 Call transcript:<br>
    <i>"Vendor: I'm not sure when the steel arrives."</i><br><br>
    ❌ No signal. No forecast. No plan.
    </div>
    """, unsafe_allow_html=True)

with col_cascade:
    st.markdown("#### CASCADE — Live")
    loss_placeholder = st.empty()
    loss_placeholder.markdown(f"""
        <div class="loss-clock-label">LIVE LOSS CLOCK</div>
        <div class="loss-clock">${st.session_state.loss_value:,.0f}</div>
    """, unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------------
# Chaos Menu
# ---------------------------------------------------------------------
st.markdown("### 🎲 Chaos Menu — pick a disaster, no pre-baked path")
menu_cols = st.columns(len(CHAOS_SCENARIOS))
for i, name in enumerate(CHAOS_SCENARIOS.keys()):
    if menu_cols[i].button(name, use_container_width=True):
        st.session_state.scenario_run = True
        st.session_state.scenario_name = name
        st.session_state.resolved = False
        st.session_state.rejection_alt = None

st.divider()

# ---------------------------------------------------------------------
# Run scenario
# ---------------------------------------------------------------------
if st.session_state.scenario_run:
    scenario = CHAOS_SCENARIOS[st.session_state.scenario_name]
    item = scenario["affected_item"]
    region = scenario["affected_region"]

    sentinel_col, reasoning_col = st.columns(2)

    # --- Sentinel feed / ReAct trace ---
    with sentinel_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("##### 📡 Sentinel Feed — ReAct Agent Trace")
        st.markdown(f"**Signal:** _{scenario['headline']}_")

        if LIVE_AGENT_AVAILABLE:
            with st.spinner("Agent reasoning live..."):
                trace = generate_react_trace_live(scenario["headline"], item, region or "Unknown Region")
        else:
            trace = generate_react_trace(scenario["headline"], item, region or "Unknown Region")

        trace_box = st.empty()
        rendered = ""
        for step_type, content in trace:
            css_class = step_type.lower()
            rendered += f'<div class="trace-line {css_class}"><b>{step_type}:</b> {content}</div>'
            trace_box.markdown(rendered, unsafe_allow_html=True)
            time.sleep(0.35)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Forecast + Reasoning trace ---
    with reasoning_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("##### 🧠 Reasoning Trace — Knowledge Graph")
        fc = forecast_delay(item, disrupted=True)
        st.markdown(f"**Forecast for {item}:**")
        st.markdown(f"- 10th percentile: `{fc['p10_date']}`")
        st.markdown(f"- 50th percentile: `{fc['p50_date']}`")
        st.markdown(f"- 90th percentile: `{fc['p90_date']}`")
        st.caption(f"Conformal coverage guarantee: ±{fc['coverage_error_pct']}% error")

        kg = traverse_knowledge_graph(item, region)
        st.markdown("**Graph traversal:**")
        for line in kg["path"]:
            st.code(line, language=None)
        if kg["recommended_alternate"]:
            st.success(f"Recommendation: switch to **{kg['recommended_alternate']}** — "
                       f"{kg['evidence_notes']}")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- CPM / Cascade impact ---
    # --- REAL CPM: forward + backward pass ---
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("##### 📉 Critical Path Impact — real ES/EF/LS/LF computation")

    baseline_cpm = run_cpm(SCHEDULE)

    delay_days = st.slider(
        "What-If Sandbox: drag the Steel Delivery delay (days)",
        min_value=0, max_value=30, value=fc["p50_days"], key="cpm_delay_slider",
    )
    disrupted_cpm = run_cpm(SCHEDULE, delay_overrides={"Steel Delivery": delay_days})

    baseline_finish = baseline_cpm["project_finish"]
    new_finish = disrupted_cpm["project_finish"]
    handover_push = new_finish - baseline_finish

    impact_c1, impact_c2 = st.columns([1, 2])
    with impact_c1:
        st.metric("Handover date pushed by", f"{handover_push} days")
        st.metric("Baseline project finish (day)", baseline_finish)
        st.metric("New project finish (day)", new_finish)
        crit_path_str = " → ".join(disrupted_cpm["critical_path"])
        st.caption(f"Critical path: {crit_path_str}")

    with impact_c2:
        acts = list(disrupted_cpm["activities"].keys())
        floats = [disrupted_cpm["activities"][a]["float"] for a in acts]
        colors = ["#ff4b4b" if disrupted_cpm["activities"][a]["critical"] else "#3fb950" for a in acts]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=acts, y=floats, marker_color=colors))
        fig.update_layout(
            template="plotly_dark", height=250,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="#11161f", plot_bgcolor="#11161f",
            yaxis_title="Float (slack) days — red = 0 float = critical path",
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Show full ES / EF / LS / LF table"):
        table_rows = []
        for name, vals in disrupted_cpm["activities"].items():
            table_rows.append({
                "Activity": name, "ES": vals["ES"], "EF": vals["EF"],
                "LS": vals["LS"], "LF": vals["LF"], "Float": vals["float"],
                "Critical": "🔴 Yes" if vals["critical"] else "🟢 No",
            })
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # --- Financial impact ---
    idle_crew_days = sum(
        disrupted_cpm["activities"][a]["EF"] - disrupted_cpm["activities"][a]["ES"]
        for a in ["HVAC Install", "Drywall"]
        if disrupted_cpm["activities"][a]["critical"]
    )
    fin = calculate_financial_impact(idle_crew_days)
    st.session_state.loss_value = fin["idle_cost"] if not st.session_state.resolved else 0
    loss_placeholder.markdown(f"""
        <div class="loss-clock-label">LIVE LOSS CLOCK</div>
        <div class="loss-clock">${st.session_state.loss_value:,.0f}</div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("##### 💰 Financial Impact")
    f1, f2, f3 = st.columns(3)
    f1.metric("Idle crew cost (if unresolved)", f"${fin['idle_cost']:,.0f}")
    f2.metric("Material cost delta (switch)", f"+${fin['material_delta']:,.0f}")
    f3.metric("Net savings if approved", f"${fin['net_savings']:,.0f}")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Portfolio Risk Heatmap ---
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("##### 🗺️ Portfolio Risk Heatmap — why this isn't just a single-project alarm")
    portfolio = get_portfolio_impact(
        disrupted_vendor="GlobalSteel_Co" if item == "Structural Steel" else "HVAC_Partners_Inc",
        disrupted_crew="Structural Crew A" if item == "Structural Steel" else "HVAC Crew A",
    )
    color_map = {"red": "#ff4b4b", "yellow": "#f2cc60", "green": "#3fb950"}
    heat_cols = st.columns(len(portfolio))
    for i, proj in enumerate(portfolio):
        heat_cols[i].markdown(f"""
            <div style="background-color:{color_map[proj['status']]}22;
                        border:1px solid {color_map[proj['status']]};
                        border-radius:6px; padding:10px; text-align:center; height:100px;">
                <div style="font-size:24px;">⬤</div>
                <div style="font-size:11px; color:{color_map[proj['status']]}; font-weight:bold;">{proj['name']}</div>
                <div style="font-size:10px; color:#8b949e;">{proj['reason']}</div>
            </div>
        """, unsafe_allow_html=True)
    st.caption("A single disruption can turn multiple projects red at once when they share a vendor or crew — "
               "this cross-project view is what a single-project workflow tool structurally can't show.")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Pareto Frontier: Cost vs Time ---
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("##### ⚖️ Cost vs. Time Tradeoff — not just one answer")
    pareto = get_pareto_options()
    pf = go.Figure()
    pf.add_trace(go.Scatter(
        x=[p["delay_days"] for p in pareto],
        y=[p["cost_delta_pct"] for p in pareto],
        mode="markers+text",
        text=[p["option"] for p in pareto],
        textposition="top center",
        marker=dict(size=14, color=["#8b949e", "#3fb950", "#f2cc60", "#ff4b4b"]),
    ))
    pf.update_layout(
        template="plotly_dark", height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="#11161f", plot_bgcolor="#11161f",
        xaxis_title="Delay (days)", yaxis_title="Material cost delta (%)",
    )
    st.plotly_chart(pf, use_container_width=True)
    st.caption("Local Supplier X sits closest to the frontier's sweet spot — lowest delay for the smallest cost jump.")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Approve / Reject flow ---
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("##### ✅ Human-in-the-Loop Decision")
    if not st.session_state.resolved:
        rc1, rc2 = st.columns(2)
        if rc1.button("✅ Approve recommended fix", type="primary", use_container_width=True):
            st.session_state.resolved = True
            st.session_state.loss_value = 0
            st.rerun()
        if rc2.button("❌ Reject — find alternate", use_container_width=True):
            st.session_state.rejection_alt = reject_and_find_alternate(item, kg["recommended_alternate"])
            st.rerun()
        if st.session_state.rejection_alt:
            alt = st.session_state.rejection_alt
            st.warning("PM rejected the first recommendation. Knowledge graph re-traversed live:")
            for line in alt["path"]:
                st.code(line, language=None)
            st.info(alt["evidence_notes"])
    else:
        st.success("Fix approved. Draft PO sent to vendor. Loss Clock reset to $0.")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("👆 Pick a scenario from the Chaos Menu to run the CASCADE engine live.")