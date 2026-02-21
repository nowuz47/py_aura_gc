"""FastAPI application with AuraGC integration."""

import asyncio
import logging
import threading
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .adapter import Python314Adapter
from .workloads import WorkloadSimulator
from .telemetry import TelemetryCollector

# Import AuraGC Core
import os
AURAGC_ENABLED_ENV = os.getenv("AURAGC_ENABLED", "true").lower() == "true"

try:
    from auragc.core.governor import Governor
    AURAGC_AVAILABLE = True
except ImportError:
    AURAGC_AVAILABLE = False
    logging.warning("auragc-core not available - running without AuraGC")

AURAGC_AVAILABLE = AURAGC_AVAILABLE and AURAGC_ENABLED_ENV

# Global instances
adapter: Python314Adapter = None
governor: Governor = None
workload_sim = WorkloadSimulator()
telemetry = TelemetryCollector()

# Background thread control
background_thread: threading.Thread = None
background_running = False


def telemetry_loop():
    """Background thread that periodically collects PSI telemetry for Baseline."""
    global background_running
    background_running = True
    
    logging.info("Standalone telemetry thread started (Baseline mode)")
    
    # Check if native sensors are available at all
    try:
        from auragc.core.sensors import get_sensors
    except ImportError:
        logging.warning("auragc.core.sensors not available. Baseline telemetry cannot read PSI pressure.")
        return

    while background_running:
        try:
            sensors = get_sensors()
            psi_data = sensors.read_psi()
            if psi_data:
                pressure, _, critical = psi_data
                telemetry.record_pressure(pressure, critical)
        except Exception as e:
            logging.error(f"Error in telemetry loop: {e}", exc_info=True)
        
        # Sleep for 1 second before next reading
        time.sleep(1.0)


def governor_loop():
    """Background thread that periodically runs the Governor (AuraGC mode)."""
    global background_running
    background_running = True
    
    logging.info("Governor thread started")
    
    while background_running:
        try:
            if governor:
                # Evaluate and apply strategy
                objects_freed = governor.tick()
                
                # Record telemetry
                strategy = governor.get_last_strategy()
                if strategy and strategy.value != "silent":
                    telemetry.record_gc_event(
                        strategy=strategy.value,
                        generation=2 if strategy.value == "aggressive" else (1 if strategy.value == "preemptive" else 0),
                        objects_freed=objects_freed,
                    )
                
                # Record pressure (if sensors available)
                from auragc.core.sensors import get_sensors
                sensors = get_sensors()
                psi_data = sensors.read_psi()
                if psi_data:
                    pressure, _, critical = psi_data
                    telemetry.record_pressure(pressure, critical)
        
        except Exception as e:
            logging.error(f"Error in governor loop: {e}", exc_info=True)
        
        # Sleep for 1 second before next evaluation
        time.sleep(1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global adapter, governor, background_thread
    
    # Startup
    logging.info("Starting AuraGC Sample Application")
    
    # Initialize adapter
    adapter = Python314Adapter()
    
    # Initialize Governor if available
    if AURAGC_AVAILABLE:
        try:
            governor = Governor(adapter)
            logging.info("AuraGC Governor initialized")
            
            # Start governor thread
            background_thread = threading.Thread(target=governor_loop, daemon=True)
            background_thread.start()
            logging.info("Governor thread started")
        except Exception as e:
            logging.error(f"Failed to initialize Governor: {e}", exc_info=True)
    else:
        logging.warning("Running without AuraGC - using default Python GC")
        # Start standalone telemetry thread for Baseline to still monitor pressure
        background_thread = threading.Thread(target=telemetry_loop, daemon=True)
        background_thread.start()
        logging.info("Standalone telemetry thread started")
    
    yield
    
    # Shutdown
    logging.info("Shutting down AuraGC Sample Application")
    global background_running
    background_running = False
    
    if background_thread:
        background_thread.join(timeout=2.0)


# Create FastAPI app
app = FastAPI(
    title="AuraGC Sample Application",
    description="FastAPI application demonstrating AuraGC integration",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AuraGC Sample Application",
        "auragc_enabled": AURAGC_AVAILABLE and governor is not None,
    }


@app.post("/allocate/ephemeral")
async def allocate_ephemeral(count: int = 10000):
    """Create many short-lived objects (simulates high-frequency API objects).
    
    Args:
        count: Number of ephemeral objects to create.
    """
    try:
        result = workload_sim.allocate_ephemeral(count)
        return {
            "status": "success",
            "message": f"Allocated {count} ephemeral objects",
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/allocate/cyclic")
async def allocate_cyclic(count: int = 1000):
    """Create objects with circular references (simulates memory leaks).
    
    This is the main "leak storm" scenario for testing AuraGC.
    
    Args:
        count: Number of cyclic object groups to create.
    """
    try:
        result = workload_sim.allocate_cyclic(count)
        return {
            "status": "success",
            "message": f"Allocated {count} cyclic object groups",
            "warning": "These objects form cycles and require GC to free",
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/allocate/static")
async def allocate_static(size_mb: int = 10):
    """Pre-load large lookup tables (simulates objects that should be frozen).
    
    Args:
        size_mb: Approximate size in MB to allocate.
    """
    try:
        result = workload_sim.allocate_static(size_mb)
        return {
            "status": "success",
            "message": f"Allocated ~{size_mb}MB of static data",
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get current heap and workload statistics.
    
    This endpoint is used by Project C (Visualizer) to monitor memory usage.
    """
    try:
        heap_usage = adapter.get_heap_usage() if adapter else {}
        workload_stats = workload_sim.get_stats()
        metrics = telemetry.get_metrics()
        
        return {
            "heap": heap_usage,
            "workload": workload_stats,
            "telemetry": metrics,
            "auragc_enabled": AURAGC_AVAILABLE and governor is not None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/telemetry")
async def get_telemetry():
    """Get full telemetry data (for monitoring/debugging)."""
    try:
        return telemetry.export_json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/gc/manual")
async def manual_gc(generation: int = 2):
    """Manually trigger GC (for testing).
    
    Args:
        generation: Generation to collect (0, 1, or 2).
    """
    try:
        if not adapter:
            raise HTTPException(status_code=503, detail="Adapter not initialized")
        
        objects_freed = adapter.trigger_gc(generation)
        return {
            "status": "success",
            "generation": generation,
            "objects_freed": objects_freed,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
