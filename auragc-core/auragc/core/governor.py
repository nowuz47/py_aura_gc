"""Adaptive Governor - Decision engine that maps environmental signals to GC strategies.

The Governor monitors PSI and cgroup sensors and decides when and how to trigger
garbage collection based on memory pressure indicators.
"""

import enum
import logging
from typing import Optional
from ..interfaces.runtime import RuntimeInterface
from .sensors import get_sensors, SensorError

logger = logging.getLogger(__name__)


class GCStrategy(enum.Enum):
    """GC collection strategies."""
    SILENT = "silent"          # Suppress GC to prioritize CPU throughput
    PREEMPTIVE = "preemptive"  # Trigger Gen 0/1 collection
    AGGRESSIVE = "aggressive"  # Trigger Gen 2 collection (Full GC)
    FREEZE = "freeze"          # Freeze current objects as immortal


class Governor:
    """Adaptive Governor that maps memory pressure to GC strategies using PI-Scoring.
    """
    
    def __init__(self, runtime: RuntimeInterface):
        self.runtime = runtime
        self.sensors = get_sensors()
        
        # Aggressive Weights for Hackathon Survival
        self.wp = 0.85  # Priority: Infrastructure Pressure (PSI)
        self.wv = 0.15  # Priority: Allocation Velocity
        
        # Safety Margins
        self.memory_limit_mb = 512.0
        self.critical_threshold_mb = 400.0  # Hard trigger at ~78% of limit
        
        # PID-style State
        self.prev_blocks = 0
        self.integral_error = 0.0
        
        # State tracking
        self.last_strategy: Optional[GCStrategy] = None
        self._has_frozen = False
        
    def calculate_urgency(self, psi_value: float, current_blocks: int) -> float:
        """
        Calculates Urgency Score (U) from 0.0 to 1.0.
        """
        # 1. Component P: Normalized PSI Pressure (0.0 - 1.0)
        p_score = psi_value

        # 2. Component V: Allocation Velocity (Blocks per second)
        delta_blocks = max(0, current_blocks - self.prev_blocks)
        v_score = min(1.0, delta_blocks / 10000.0)  # Normalized to a 10k block spike
        self.prev_blocks = current_blocks

        # 3. Component S: Static Safety Margin (Critical override)
        # Assuming 1 block approx 100 bytes for estimation (as used in dashboard)
        estimated_mb = (current_blocks * 100) / (1024 * 1024)
        s_score = 1.0 if estimated_mb > self.critical_threshold_mb else 0.0

        # Weighted Sum + Integral Error (Memory Debt)
        u = (self.wp * p_score) + (self.wv * v_score)
        
        # Force Critical if we exceed the Safety Margin
        if estimated_mb > self.critical_threshold_mb:
            logger.warning(f"Safety Margin Exceeded: {estimated_mb:.1f}MB > {self.critical_threshold_mb}MB")
            
        return max(u, s_score)

    def evaluate(self) -> GCStrategy:
        """Evaluate current memory pressure and return appropriate strategy."""
        
        # Check cgroup critical state first (highest priority)
        cgroup_critical = self.sensors.is_cgroup_critical()
        if cgroup_critical is True:
            logger.warning("Cgroup critical state detected - triggering AGGRESSIVE GC (Will Freeze)")
            return GCStrategy.AGGRESSIVE
            
        heap_stats = self.runtime.get_heap_usage()
        current_blocks = heap_stats.get("allocated_blocks", 0)
        
        # Read PSI pressure
        psi_data = self.sensors.read_psi()
        if psi_data is not None:
            some_pressure, full_pressure, psi_critical = psi_data
            current_pressure = max(some_pressure, full_pressure)
            
            # Aggressive Urgency Scaling: Immediately spike on any real pressure above 1%
            if current_pressure >= 0.01:
                current_pressure = max(current_pressure, 0.85)
        else:
            # PSI unavailable - attempt Cgroup fallback
            cgroup_pressure = self.sensors.read_cgroup_pressure()
            if cgroup_pressure is not None:
                current_pressure = cgroup_pressure
                psi_critical = False
            else:
                return GCStrategy.SILENT
                
        # Calculate Final Urgency
        u = self.calculate_urgency(current_pressure, current_blocks)
        
        if u >= 0.8 or psi_critical:
            logger.warning(f"Critical Urgency ({u:.2f}) - AGGRESSIVE (Will Freeze)")
            return GCStrategy.AGGRESSIVE
        elif u >= 0.5:
            logger.info(f"High Urgency ({u:.2f}) - PREEMPTIVE GC")
            return GCStrategy.PREEMPTIVE
        
        return GCStrategy.SILENT
    
    def apply_strategy(self, strategy: GCStrategy) -> int:
        """Apply a GC strategy by calling the runtime adapter."""
        self.last_strategy = strategy
        
        if strategy == GCStrategy.SILENT:
            return 0
            
        elif strategy == GCStrategy.PREEMPTIVE:
            freed_0 = self.runtime.trigger_gc(0)
            freed_1 = self.runtime.trigger_gc(1)
            return freed_0 + freed_1
            
        elif strategy == GCStrategy.AGGRESSIVE or strategy == GCStrategy.FREEZE:
            # Full GC (Gen 2)
            freed = self.runtime.trigger_gc(2)
            logger.info(f"AGGRESSIVE GC: freed {freed} objects")
            
            # Refined Immortal Branding: Call freeze immediately after survival
            if strategy == GCStrategy.FREEZE or not self._has_frozen:
                self.runtime.apply_freeze()
                self._has_frozen = True
                logger.info("FREEZE: Applied immortal branding to current objects to protect next cycle")
            return freed
            
        return 0
    
    def tick(self) -> int:
        """Evaluate current conditions and apply appropriate strategy."""
        strategy = self.evaluate()
        return self.apply_strategy(strategy)
    
    def get_last_strategy(self) -> Optional[GCStrategy]:
        return self.last_strategy
