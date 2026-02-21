"""Telemetry and metrics export for monitoring."""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """Collects and exports telemetry data for monitoring."""
    
    def __init__(self):
        """Initialize the telemetry collector."""
        self.start_time = time.time()
        self.gc_events = []
        self.pressure_readings = []
        self.max_history = 1000  # Keep last 1000 readings
    
    def record_gc_event(self, strategy: str, generation: int, objects_freed: int):
        """Record a GC event.
        
        Args:
            strategy: GC strategy used (e.g., "AGGRESSIVE", "PREEMPTIVE").
            generation: Generation collected (0, 1, or 2).
            objects_freed: Number of objects freed.
        """
        event = {
            "timestamp": time.time(),
            "strategy": strategy,
            "generation": generation,
            "objects_freed": objects_freed,
        }
        self.gc_events.append(event)
        
        # Trim history
        if len(self.gc_events) > self.max_history:
            self.gc_events = self.gc_events[-self.max_history:]
    
    def record_pressure(self, pressure: float, critical: bool):
        """Record a pressure reading.
        
        Args:
            pressure: Current pressure (0.0-1.0).
            critical: Whether pressure is critical.
        """
        reading = {
            "timestamp": time.time(),
            "pressure": pressure,
            "critical": critical,
        }
        self.pressure_readings.append(reading)
        
        # Trim history
        if len(self.pressure_readings) > self.max_history:
            self.pressure_readings = self.pressure_readings[-self.max_history:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary.
        
        Returns:
            dict: Summary metrics.
        """
        uptime = time.time() - self.start_time
        
        # Count GC events by strategy
        strategy_counts = {}
        total_gc_events = len(self.gc_events)
        total_objects_freed = 0
        
        for event in self.gc_events:
            strategy = event["strategy"]
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            total_objects_freed += event.get("objects_freed", 0)
        
        # Average pressure
        avg_pressure = 0.0
        if self.pressure_readings:
            avg_pressure = sum(r["pressure"] for r in self.pressure_readings) / len(self.pressure_readings)
        
        return {
            "uptime_seconds": uptime,
            "gc_events_total": total_gc_events,
            "gc_events_by_strategy": strategy_counts,
            "objects_freed_total": total_objects_freed,
            "average_pressure": avg_pressure,
            "pressure_readings_count": len(self.pressure_readings),
        }
    
    def export_json(self) -> Dict[str, Any]:
        """Export telemetry data as JSON-serializable dict.
        
        Returns:
            dict: Full telemetry data.
        """
        return {
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "current_time": datetime.now().isoformat(),
            "metrics": self.get_metrics(),
            "recent_gc_events": self.gc_events[-100:],  # Last 100 events
            "recent_pressure_readings": self.pressure_readings[-100:],  # Last 100 readings
        }
