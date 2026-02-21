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


def create_memory_chart(baseline_data, auragc_data):
    """Create memory usage comparison chart."""
    fig = go.Figure()
    
    if baseline_data and baseline_data.get("status") == "online":
        baseline_mem = get_memory_usage(baseline_data)
        if baseline_mem:
            fig.add_trace(go.Scatter(
                x=[baseline_data["timestamp"]],
                y=[baseline_mem["estimated_mb"]],
                mode='lines+markers',
                name='Baseline (Default GC)',
                line=dict(color='red', width=2),
            ))
    
    if auragc_data and auragc_data.get("status") == "online":
        auragc_mem = get_memory_usage(auragc_data)
        if auragc_mem:
            fig.add_trace(go.Scatter(
                x=[auragc_data["timestamp"]],
                y=[auragc_mem["estimated_mb"]],
                mode='lines+markers',
                name='AuraGC Enabled',
                line=dict(color='green', width=2),
            ))
    
    fig.update_layout(
        title="Memory Usage Over Time",
        xaxis_title="Time",
        yaxis_title="Estimated Memory (MB)",
        hovermode='x unified',
        height=400,
    )
    
    # Add 512MB limit line (container limit)
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


# Main dashboard
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

# Charts
st.subheader("Memory Usage Comparison")
memory_chart = create_memory_chart(baseline_stats, auragc_stats)
st.plotly_chart(memory_chart, use_container_width=True)

st.subheader("GC Events Comparison")
gc_chart = create_gc_events_chart(baseline_stats, auragc_stats)
st.plotly_chart(gc_chart, use_container_width=True)

# Auto-refresh
if st.checkbox("Auto-refresh (5s)", value=True):
    time.sleep(5)
    st.rerun()

# Manual refresh button
if st.button("Refresh Now"):
    st.cache_data.clear()
    st.rerun()
