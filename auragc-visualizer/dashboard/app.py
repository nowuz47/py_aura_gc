"""Streamlit dashboard for AuraGC visualization."""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time
import json

# Configuration
BASELINE_URL = "http://baseline:8000"
AURAGC_URL = "http://auragc:8000"
LOCUST_URL = "http://locust:8089"

# Allow override via environment
import os
BASELINE_URL = os.getenv("BASELINE_URL", "http://localhost:8001")
AURAGC_URL = os.getenv("AURAGC_URL", "http://localhost:8002")
LOCUST_URL = os.getenv("LOCUST_URL", "http://locust:8089")

# Scoring constants
MEMORY_LIMIT_MB = 512
MEMORY_GOOD_THRESHOLD_MB = 256
STABILITY_FULL_SECONDS = 300
SCORE_WEIGHTS = {
    "memory_efficiency": 0.30,
    "gc_effectiveness": 0.25,
    "pressure_handling": 0.15,
    "process_health": 0.25,
    "stability": 0.05,
}

st.set_page_config(page_title="AuraGC Dashboard", layout="wide")

st.title("AuraGC Performance Dashboard")
st.markdown("Real-time comparison of Default GC vs AuraGC-enabled runtime")


@st.cache_data(ttl=1)
def fetch_stats(url: str, label: str):
    """Fetch stats from a service."""
    try:
        response = requests.get(f"{url}/stats", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return {
                "label": label,
                "url": url,
                "data": data,
                "status": "online",
                "timestamp": datetime.now(),
            }
    except Exception as e:
        return {
            "label": label,
            "url": url,
            "status": "offline",
            "error": str(e),
            "timestamp": datetime.now(),
        }
    return None


def get_memory_usage(data):
    """Extract memory usage from stats."""
    if not data or data.get("status") != "online":
        return None
    
    heap = data.get("data", {}).get("heap", {})
    allocated_blocks = heap.get("allocated_blocks", 0)
    gen_counts = heap.get("gen_counts", [0, 0, 0])
    
    # Estimate memory (rough approximation)
    # Each block ~100 bytes on average
    estimated_mb = (allocated_blocks * 100) / (1024 * 1024)
    
    return {
        "allocated_blocks": allocated_blocks,
        "estimated_mb": estimated_mb,
        "gen_counts": gen_counts,
    }





def create_memory_chart(baseline_data, auragc_data, memory_history=None):
    """Create memory usage comparison chart. Uses memory_history if provided for time-series."""
    fig = go.Figure()
    history = memory_history or []

    if len(history) > 0:
        ts = [h["ts"] for h in history]
        baseline_ys = [h.get("baseline_mb") for h in history]
        auragc_ys = [h.get("auragc_mb") for h in history]
        if any(b is not None for b in baseline_ys):
            fig.add_trace(go.Scatter(
                x=ts,
                y=baseline_ys,
                mode="lines+markers",
                name="Baseline (Default GC)",
                line=dict(color="red", width=2),
                connectgaps=False,
            ))
        if any(a is not None for a in auragc_ys):
            fig.add_trace(go.Scatter(
                x=ts,
                y=auragc_ys,
                mode="lines+markers",
                name="AuraGC Enabled",
                line=dict(color="green", width=2),
                connectgaps=False,
            ))
    else:
        if baseline_data and baseline_data.get("status") == "online":
            baseline_mem = get_memory_usage(baseline_data)
            if baseline_mem:
                fig.add_trace(go.Scatter(
                    x=[baseline_data["timestamp"]],
                    y=[baseline_mem["estimated_mb"]],
                    mode="lines+markers",
                    name="Baseline (Default GC)",
                    line=dict(color="red", width=2),
                ))
        if auragc_data and auragc_data.get("status") == "online":
            auragc_mem = get_memory_usage(auragc_data)
            if auragc_mem:
                fig.add_trace(go.Scatter(
                    x=[auragc_data["timestamp"]],
                    y=[auragc_mem["estimated_mb"]],
                    mode="lines+markers",
                    name="AuraGC Enabled",
                    line=dict(color="green", width=2),
                ))

    fig.update_layout(
        title="Memory Usage Over Time",
        xaxis_title="Time",
        yaxis_title="Estimated Memory (MB)",
        hovermode="x unified",
        height=400,
    )
    fig.add_hline(y=512, line_dash="dash", line_color="orange",
                  annotation_text="Container Limit (512MB)")
    return fig





# Session state for memory history and restart tracking
if "memory_history" not in st.session_state:
    st.session_state["memory_history"] = []
if "restarts" not in st.session_state:
    st.session_state["restarts"] = {"baseline": 0, "auragc": 0}
if "last_uptime" not in st.session_state:
    st.session_state["last_uptime"] = {"baseline": None, "auragc": None}

MAX_HISTORY_POINTS = 60

# --- Fetch Data Early for Top-Level Charts ---
baseline_stats = fetch_stats(BASELINE_URL, "Baseline")
auragc_stats = fetch_stats(AURAGC_URL, "AuraGC")

now = time.time()
baseline_mb = None
auragc_mb = None

# Update Baseline State
if baseline_stats and baseline_stats.get("status") == "online":
    telemetry = baseline_stats.get("data", {}).get("telemetry", {})
    uptime = telemetry.get("uptime_seconds", 0)
    last_up = st.session_state["last_uptime"]["baseline"]
    if last_up is not None and uptime < last_up - 2:
        st.session_state["restarts"]["baseline"] += 1
    st.session_state["last_uptime"]["baseline"] = uptime

    m = get_memory_usage(baseline_stats)
    if m:
        baseline_mb = m["estimated_mb"]

# Update AuraGC State
if auragc_stats and auragc_stats.get("status") == "online":
    telemetry = auragc_stats.get("data", {}).get("telemetry", {})
    uptime = telemetry.get("uptime_seconds", 0)
    last_up = st.session_state["last_uptime"]["auragc"]
    if last_up is not None and uptime < last_up - 2:
        st.session_state["restarts"]["auragc"] += 1
    st.session_state["last_uptime"]["auragc"] = uptime

    m = get_memory_usage(auragc_stats)
    if m:
        auragc_mb = m["estimated_mb"]

if baseline_mb is not None or auragc_mb is not None:
    st.session_state["memory_history"].append({
        "ts": now,
        "baseline_mb": baseline_mb,
        "auragc_mb": auragc_mb,
    })
    st.session_state["memory_history"] = st.session_state["memory_history"][-MAX_HISTORY_POINTS:]

    # Log to file for external monitoring
    baseline_mb_str = f"{baseline_mb:.2f} MB" if baseline_mb is not None else "Offline/NA"
    auragc_mb_str = f"{auragc_mb:.2f} MB" if auragc_mb is not None else "Offline/NA"
    try:
        with open("container_status.log", "a") as f:
            f.write(f"{datetime.now().isoformat()} - Baseline: {baseline_mb_str} | AuraGC: {auragc_mb_str}\n")
    except Exception as e:
        pass

def fetch_locust_stats():
    try:
        res = requests.get(f"{LOCUST_URL}/stats/requests", timeout=2)
        if res.status_code == 200:
            return res.json().get("stats", [])
    except Exception:
        pass
    return []

def set_locust_swarm(users, spawn_rate):
    try:
        data = {"user_count": users, "spawn_rate": spawn_rate, "host": "http://localhost"}
        requests.post(f"{LOCUST_URL}/swarm", data=data, timeout=2)
    except Exception:
        pass

def stop_locust():
    try:
        requests.get(f"{LOCUST_URL}/stop", timeout=2)
    except Exception:
        pass

# --- Test 1: Leak Storm ---
st.markdown("---")
st.header("1️⃣ Test 1: Leak Storm (Resilience)")
st.markdown("Simulates memory leak via circular references. **Winning Metric**: Uptime & Survival without OOM.")

col_btn1, col_content1 = st.columns([1, 4])
with col_btn1:
    if st.button("▶️ Start Leak Storm", use_container_width=True):
        st.session_state["active_test"] = "leak_storm"
        requests.post(f"{LOCUST_URL}/test_mode", data={"mode": "leak_storm"}, timeout=2)
        set_locust_swarm(50, 10)
        st.success("Test 1 Started")
    if st.button("🛑 Stop Traffic", key="stop1", use_container_width=True):
        st.session_state["active_test"] = None
        stop_locust()

with col_content1:
    st.subheader("Memory Track & Tombstones")
    memory_chart = create_memory_chart(
        baseline_stats, auragc_stats,
        memory_history=st.session_state.get("memory_history"),
    )
    st.plotly_chart(memory_chart, use_container_width=True)
    
    tomb_col1, tomb_col2 = st.columns(2)
    with tomb_col1:
        restarts_base = st.session_state["restarts"]["baseline"]
        st.error(f"**Baseline OOM Restarts:** {restarts_base}")
        if restarts_base > 0:
            st.write("🪦 " * restarts_base)
    with tomb_col2:
        restarts_aura = st.session_state["restarts"]["auragc"]
        st.success(f"**AuraGC OOM Restarts:** {restarts_aura}")
        if restarts_aura > 0:
            st.write("🪦 " * restarts_aura)

# --- Test 2: Tail Latency Jitter ---
st.markdown("---")
st.header("2️⃣ Test 2: Tail Latency Jitter (Predictability)")
st.markdown("Steady stream of lightweight API requests against a 300MB warm-up dataset. **Winning Metric**: P95 & P99 Latency Profile.")

col_btn2, col_content2 = st.columns([1, 4])
with col_btn2:
    if st.button("▶️ Start Jitter Test", use_container_width=True):
        st.session_state["active_test"] = "jitter"
        try:
            requests.post(f"{BASELINE_URL}/allocate/static?size_mb=300", timeout=5)
            requests.post(f"{AURAGC_URL}/allocate/static?size_mb=300", timeout=5)
        except Exception:
            pass
        requests.post(f"{LOCUST_URL}/test_mode", data={"mode": "jitter"}, timeout=2)
        set_locust_swarm(20, 5)
        st.success("Test 2 Started")
    if st.button("🛑 Stop Traffic", key="stop2", use_container_width=True):
        st.session_state["active_test"] = None
        stop_locust()

with col_content2:
    st.subheader("Latency Histogram (P95 / P99)")
    locust_stats_data = fetch_locust_stats()
    base_jitter = next((s for s in locust_stats_data if s.get("name") == "Baseline: Jitter Ping"), None)
    aura_jitter = next((s for s in locust_stats_data if s.get("name") == "AuraGC: Jitter Ping"), None)
    
    if base_jitter or aura_jitter:
        models = ["Baseline", "AuraGC"]
        p95s = [base_jitter.get("response_time_percentile_0.95", 0) if base_jitter else 0,
                aura_jitter.get("response_time_percentile_0.95", 0) if aura_jitter else 0]
        p99s = [base_jitter.get("response_time_percentile_0.99", 0) if base_jitter else 0,
                aura_jitter.get("response_time_percentile_0.99", 0) if aura_jitter else 0]
        
        fig_lat = go.Figure()
        fig_lat.add_trace(go.Bar(name='P95 Latency', x=models, y=p95s, marker_color=['#ff9999', '#99ff99']))
        fig_lat.add_trace(go.Bar(name='P99 Latency', x=models, y=p99s, marker_color=['#cc0000', '#00cc00']))
        fig_lat.update_layout(barmode='group', title="Tail Latency in milliseconds (Lower is Better)", yaxis_title="ms")
        st.plotly_chart(fig_lat, use_container_width=True)
    else:
        st.info("No Jitter test data available yet. Start the test to see latency metrics.")

# --- Test 3: Throughput Peak ---
st.markdown("---")
st.header("3️⃣ Test 3: Throughput Peak (Efficiency)")
st.markdown("Variable traffic load (sine wave) focusing on fast ephemeral allocations. **Winning Metric**: Request Throughput tracking during Peak Traffic.")

col_btn3, col_content3 = st.columns([1, 4])
with col_btn3:
    if st.button("▶️ Start Throughput Test", use_container_width=True):
        st.session_state["active_test"] = "throughput"
        st.session_state["throughput_start_time"] = time.time()
        requests.post(f"{LOCUST_URL}/test_mode", data={"mode": "throughput"}, timeout=2)
        set_locust_swarm(10, 5)
        st.success("Test 3 Started")
    if st.button("🛑 Stop Traffic", key="stop3", use_container_width=True):
        st.session_state["active_test"] = None
        stop_locust()

with col_content3:
    st.subheader("Requests Per Second (RPS)")
    base_heavy = next((s for s in locust_stats_data if s.get("name") == "Baseline: Heavy Ping"), None)
    aura_heavy = next((s for s in locust_stats_data if s.get("name") == "AuraGC: Heavy Ping"), None)
    
    if base_heavy or aura_heavy:
        b_rps = base_heavy.get("current_rps", 0) if base_heavy else 0
        a_rps = aura_heavy.get("current_rps", 0) if aura_heavy else 0
        
        fig_rps = go.Figure()
        fig_rps.add_trace(go.Indicator(
            mode="number", value=b_rps, title={"text": "Baseline RPS"},
            domain={'x': [0, 0.45], 'y': [0, 1]}, number={"font": {"color": "red"}}
        ))
        fig_rps.add_trace(go.Indicator(
            mode="number", value=a_rps, title={"text": "AuraGC RPS"},
            domain={'x': [0.55, 1], 'y': [0, 1]}, number={"font": {"color": "green"}}
        ))
        st.plotly_chart(fig_rps, use_container_width=True)
    else:
        st.info("No Throughput test data available. Start the test to see RPS metrics.")

# Dynamic throughput traffic shaper via Streamlit auto-refresh
if st.session_state.get("active_test") == "throughput":
    import math
    t = time.time() - st.session_state.get("throughput_start_time", time.time())
    users = int(10 + 90 * ((math.sin(t * (2 * math.pi / 30)) + 1) / 2))
    set_locust_swarm(users, 20)

# Auto-refresh
if st.checkbox("Auto-refresh (5s)", value=True):
    time.sleep(5)
    st.rerun()

# Manual refresh button
if st.button("Refresh Now"):
    st.cache_data.clear()
    st.rerun()
