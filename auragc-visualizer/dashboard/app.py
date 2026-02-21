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

# Allow override via environment
import os
BASELINE_URL = os.getenv("BASELINE_URL", "http://localhost:8001")
AURAGC_URL = os.getenv("AURAGC_URL", "http://localhost:8002")

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


def score_memory_efficiency(estimated_mb: float, limit_mb: float = MEMORY_LIMIT_MB) -> int:
    """Score 0-100: 100 when below MEMORY_GOOD_THRESHOLD_MB, linear decay to 0 at limit_mb."""
    if estimated_mb <= MEMORY_GOOD_THRESHOLD_MB:
        return 100
    if estimated_mb >= limit_mb:
        return 0
    return int(100 * (limit_mb - estimated_mb) / (limit_mb - MEMORY_GOOD_THRESHOLD_MB))


def score_gc_effectiveness(gc_events_total: int, objects_freed_total: int) -> int:
    """Score 0-100: based on objects freed per GC event; 50 if no events."""
    if gc_events_total == 0:
        return 50
    ratio = objects_freed_total / gc_events_total
    # Normalize: e.g. 10+ objects per event = 100, 0 = 0
    score = min(100, int(ratio * 10))
    return max(0, score)


def score_pressure(average_pressure: float):
    """Score 0-100: 100 - pressure*100. Returns None if N/A."""
    if average_pressure is None:
        return None
    return max(0, min(100, int(100 - (average_pressure * 100))))


def score_health(online: bool) -> int:
    """Score 0-100: 100 if online, 0 if offline."""
    return 100 if online else 0


def score_stability(uptime_seconds: float) -> int:
    """Score 0-100: 100 at STABILITY_FULL_SECONDS+, linear below."""
    if uptime_seconds >= STABILITY_FULL_SECONDS:
        return 100
    return min(100, int(100 * uptime_seconds / STABILITY_FULL_SECONDS))


def overall_score(components: dict, weights: dict, skip_none: bool = True) -> int:
    """Weighted average of component scores; skip None if skip_none."""
    total_weight = 0.0
    weighted_sum = 0.0
    for key, weight in weights.items():
        val = components.get(key)
        if val is None and skip_none:
            continue
        if val is not None:
            weighted_sum += val * weight
            total_weight += weight
    if total_weight <= 0:
        return 0
    return int(weighted_sum / total_weight)


def compute_scores(stats_data, is_auragc: bool) -> dict:
    """Compute all component scores from stats response. Returns dict of component name -> score (or None)."""
    online = stats_data and stats_data.get("status") == "online"
    if not online:
        return {
            "memory_efficiency": 0,
            "gc_effectiveness": 50,
            "pressure_handling": 0,
            "process_health": 0,
            "stability": 0,
        }

    data = stats_data.get("data") or {}
    heap = data.get("heap", {})
    telemetry = data.get("telemetry", {})

    mem = get_memory_usage(stats_data)
    estimated_mb = mem["estimated_mb"] if mem else 0

    gc_total = telemetry.get("gc_events_total", 0)
    objects_freed = telemetry.get("objects_freed_total", 0)
    uptime = telemetry.get("uptime_seconds", 0)
    avg_pressure = telemetry.get("average_pressure")

    return {
        "memory_efficiency": score_memory_efficiency(estimated_mb),
        "gc_effectiveness": score_gc_effectiveness(gc_total, objects_freed),
        "pressure_handling": score_pressure(avg_pressure),
        "process_health": score_health(True),
        "stability": score_stability(uptime),
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


def create_gc_events_chart(baseline_data, auragc_data):
    """Create GC events comparison chart."""
    fig = go.Figure()
    
    if baseline_data and baseline_data.get("status") == "online":
        telemetry = baseline_data.get("data", {}).get("telemetry", {})
        gc_total = telemetry.get("gc_events_total", 0)
        fig.add_trace(go.Bar(
            x=["Baseline"],
            y=[gc_total],
            name="Baseline GC Events",
            marker_color='red',
        ))
    
    if auragc_data and auragc_data.get("status") == "online":
        telemetry = auragc_data.get("data", {}).get("telemetry", {})
        gc_total = telemetry.get("gc_events_total", 0)
        gc_by_strategy = telemetry.get("gc_events_by_strategy", {})
        
        fig.add_trace(go.Bar(
            x=["AuraGC"],
            y=[gc_total],
            name="AuraGC Total Events",
            marker_color='green',
        ))
    
    fig.update_layout(
        title="GC Events Comparison",
        xaxis_title="Runtime",
        yaxis_title="Total GC Events",
        height=300,
    )
    
    return fig


# Session state for memory history (optional time-series)
if "memory_history" not in st.session_state:
    st.session_state["memory_history"] = []
MAX_HISTORY_POINTS = 60

st.subheader("AuraGC Strategy Control")
strategy_col1, strategy_col2 = st.columns([3, 1])
with strategy_col1:
    selected_strategy = st.selectbox(
        "Select Strategy", 
        ["Auto", "Silent", "Preemptive", "Aggressive", "Freeze"],
        help="'Auto' lets the Governor decide based on memory pressure. Other options force the strategy."
    )
with strategy_col2:
    st.write("") # Layout spacing
    st.write("") # Layout spacing
    if st.button("Apply Strategy", use_container_width=True):
        try:
            res = requests.post(f"{AURAGC_URL}/gc/strategy", params={"strategy": selected_strategy.lower()}, timeout=2)
            if res.status_code == 200:
                st.success(f"Strategy overriding set to **{selected_strategy}**")
            else:
                st.error(f"Failed to set strategy: {res.text}")
        except Exception as e:
            st.error(f"Error connecting to AuraGC: {e}")

st.markdown("---")

st.subheader("Locust Load Generator")
st.write("Use the embedded Locust load tester to direct identical traffic to both **Baseline** and **AuraGC** simultaneously.")

LOCUST_URL = "http://locust:8089"

def set_locust_swarm(users, spawn_rate):
    try:
        data = {
            "user_count": users,
            "spawn_rate": spawn_rate,
            "host": "http://localhost" # Arbitrary, since locustfile ignores it now
        }
        res = requests.post(f"{LOCUST_URL}/swarm", data=data, timeout=2)
        return res.status_code == 200
    except Exception as e:
        st.error(f"Error connecting to Locust API: {e}")
        return False

def stop_locust():
    try:
        res = requests.get(f"{LOCUST_URL}/stop", timeout=2)
        return res.status_code == 200
    except Exception as e:
        st.error(f"Error stopping Locust: {e}")
        return False


load_col1, load_col2, load_col3, load_col4 = st.columns(4)

with load_col1:
    if st.button("Stop Traffic", use_container_width=True):
        if stop_locust():
            st.success("Traffic stopped.")
with load_col2:
    if st.button("Low Traffic", use_container_width=True, type="secondary"):
        if set_locust_swarm(5, 1):
            st.success("Low load started (5 users)")
with load_col3:
    if st.button("Medium Traffic", use_container_width=True, type="secondary"):
        if set_locust_swarm(25, 5):
            st.success("Medium load started (25 users)")
with load_col4:
    if st.button("High Traffic", use_container_width=True, type="primary"):
        if set_locust_swarm(100, 10):
            st.success("High load started (100 users)")

try:
    locust_stats = requests.get(f"{LOCUST_URL}/stats/requests", timeout=2).json()
    state = locust_stats.get("state", "unknown")
    if state == "running":
        st.info(f"Locust is **RUNNING** with {locust_stats.get('user_count', 0)} active users.")
    elif state == "stopped" or state == "ready":
        st.info("Locust is **IDLE**.")
except Exception:
    st.warning("Could not reach Locust container.")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Baseline (Default GC)")
    baseline_stats = fetch_stats(BASELINE_URL, "Baseline")
    if baseline_stats:
        if baseline_stats["status"] == "online":
            st.success("Online")
            heap = baseline_stats["data"].get("heap", {})
            st.metric("Allocated Blocks", heap.get("allocated_blocks", 0))
            mem = get_memory_usage(baseline_stats)
            if mem:
                st.metric("Estimated Memory", f"{mem['estimated_mb']:.2f} MB")
        else:
            st.error(f"Offline: {baseline_stats.get('error', 'Unknown error')}")

with col2:
    st.subheader("AuraGC Enabled")
    auragc_stats = fetch_stats(AURAGC_URL, "AuraGC")
    if auragc_stats:
        if auragc_stats["status"] == "online":
            st.success("Online")
            heap = auragc_stats["data"].get("heap", {})
            st.metric("Allocated Blocks", heap.get("allocated_blocks", 0))
            mem = get_memory_usage(auragc_stats)
            if mem:
                st.metric("Estimated Memory", f"{mem['estimated_mb']:.2f} MB")
            
            # Show GC strategy breakdown
            telemetry = auragc_stats["data"].get("telemetry", {})
            gc_by_strategy = telemetry.get("gc_events_by_strategy", {})
            if gc_by_strategy:
                st.write("**GC Strategies:**")
                for strategy, count in gc_by_strategy.items():
                    st.write(f"- {strategy}: {count}")
        else:
            st.error(f"Offline: {auragc_stats.get('error', 'Unknown error')}")

# Append to memory history
now = time.time()
baseline_mb = None
auragc_mb = None
if baseline_stats and baseline_stats.get("status") == "online":
    m = get_memory_usage(baseline_stats)
    if m:
        baseline_mb = m["estimated_mb"]
if auragc_stats and auragc_stats.get("status") == "online":
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

# Overall scores
baseline_scores = compute_scores(baseline_stats, is_auragc=False)
auragc_scores = compute_scores(auragc_stats, is_auragc=True)
overall_baseline = overall_score(baseline_scores, SCORE_WEIGHTS)
overall_auragc = overall_score(auragc_scores, SCORE_WEIGHTS)

score_col1, score_col2 = st.columns(2)
with score_col1:
    st.metric("Overall Score (Baseline)", f"{overall_baseline}/100")
    st.progress(overall_baseline / 100.0)
with score_col2:
    st.metric("Overall Score (AuraGC)", f"{overall_auragc}/100")
    st.progress(overall_auragc / 100.0)

# Performance breakdown
st.subheader("Performance breakdown")
break_col1, break_col2 = st.columns(2)

with break_col1:
    st.write("**Baseline (Default GC)**")
    for name, key in [
        ("Memory efficiency", "memory_efficiency"),
        ("GC effectiveness", "gc_effectiveness"),
        ("Pressure handling", "pressure_handling"),
        ("Process health", "process_health"),
        ("Stability", "stability"),
    ]:
        val = baseline_scores.get(key)
        if val is None:
            st.write(f"- {name}: N/A")
        else:
            st.write(f"- {name}: {val}/100")
            st.progress(val / 100.0)

with break_col2:
    st.write("**AuraGC Enabled**")
    for name, key in [
        ("Memory efficiency", "memory_efficiency"),
        ("GC effectiveness", "gc_effectiveness"),
        ("Pressure handling", "pressure_handling"),
        ("Process health", "process_health"),
        ("Stability", "stability"),
    ]:
        val = auragc_scores.get(key)
        if val is None:
            st.write(f"- {name}: N/A")
        else:
            st.write(f"- {name}: {val}/100")
            st.progress(val / 100.0)

# Collapsible scoring guide
with st.expander("Scoring guide"):
    st.markdown("""
- **Memory efficiency**: 100 when estimated memory < 256 MB; linear decay to 0 at 512 MB (container limit).
- **GC effectiveness**: Based on objects freed per GC event; 50 if no events.
- **Pressure handling**: 100 - (average pressure × 100). AuraGC only; Baseline N/A.
- **Process health**: 100 if online, 0 if offline.
- **Stability**: 100 after 300 s uptime; linear 0–100 below.
- **Overall**: Weighted average (Memory 30%, GC 25%, Pressure 15%, Health 25%, Stability 5%). Pressure omitted for Baseline.
    """)

# Charts
st.subheader("Memory Usage Comparison")
memory_chart = create_memory_chart(
    baseline_stats, auragc_stats,
    memory_history=st.session_state.get("memory_history"),
)
st.plotly_chart(memory_chart, use_container_width=True)

st.subheader("GC Events Comparison")
gc_chart = create_gc_events_chart(baseline_stats, auragc_stats)
st.plotly_chart(gc_chart, use_container_width=True)

st.subheader("Performance Logs / AI Data")
with st.expander("View Raw Telemetry & Diagnostic Data"):
    log_col1, log_col2 = st.columns(2)
    with log_col1:
        st.write("**Baseline Diagnostics**")
        if baseline_stats and baseline_stats.get("status") == "online":
            st.json(baseline_stats.get("data", {}))
        else:
            st.write("Offline or Unavailable")
    with log_col2:
        st.write("**AuraGC Diagnostics**")
        if auragc_stats and auragc_stats.get("status") == "online":
            st.json(auragc_stats.get("data", {}))
        else:
            st.write("Offline or Unavailable")

# Auto-refresh
if st.checkbox("Auto-refresh (5s)", value=True):
    time.sleep(5)
    st.rerun()

# Manual refresh button
if st.button("Refresh Now"):
    st.cache_data.clear()
    st.rerun()
