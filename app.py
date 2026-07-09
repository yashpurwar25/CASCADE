"""
app.py
CASCADE War Room — Streamlit demo UI.
Run with: streamlit run app.py
"""

import time
import streamlit as st
import plotly.graph_objects as go

from mock_data import CHAOS_SCENARIOS, VENDORS
from engine import (
    forecast_delay,
    calculate_cascade_impact,
    traverse_knowledge_graph,
    generate_react_trace,
    calculate_financial_impact,
)

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

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
st.title("🛡 CASCADE — Cognitive Supply Chain Resilience Engine")
st.caption("From reactive tracking to proactive, agentic intelligence.")

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
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("##### 📉 Critical Path Impact")
    cascade = calculate_cascade_impact(fc["p50_days"])
    impact_c1, impact_c2 = st.columns([1, 2])
    with impact_c1:
        st.metric("Handover date pushed by", f"{cascade['handover_push_days']} days")
        st.metric("Idle crew-days", cascade["idle_crew_days"])
    with impact_c2:
        fig = go.Figure()
        activities = list(cascade["affected_activities"])
        fig.add_trace(go.Bar(
            x=[a["activity"] for a in activities],
            y=[a["pushed_days"] for a in activities],
            marker_color="#ff4b4b",
        ))
        fig.update_layout(
            template="plotly_dark", height=250,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="#11161f", plot_bgcolor="#11161f",
            yaxis_title="Days pushed",
        )
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Financial impact ---
    fin = calculate_financial_impact(cascade["idle_crew_days"])
    st.session_state.loss_value = fin["idle_cost"]
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

    if not st.session_state.resolved:
        if st.button("✅ Approve recommended fix (PM action)", type="primary"):
            st.session_state.resolved = True
            st.session_state.loss_value = 0
            st.rerun()
    else:
        st.success("Fix approved. Draft PO sent to vendor. Loss Clock reset to $0.")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("👆 Pick a scenario from the Chaos Menu to run the CASCADE engine live.")