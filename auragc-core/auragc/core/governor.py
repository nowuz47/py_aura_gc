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
    """Adaptive Governor that maps memory pressure to GC strategies.
    
    The Governor monitors PSI (Pressure Stall Information) and cgroup events,
    then triggers appropriate GC actions via the RuntimeInterface.
    """
    
    def __init__(self, runtime: RuntimeInterface):
        """Initialize the Governor with a runtime adapter.
        
        Args:
            runtime: Implementation of RuntimeInterface to control GC.
        """
        self.runtime = runtime
        self.sensors = get_sensors()
        
        # Pressure thresholds (0.0-1.0)
        self.pressure_threshold_preemptive = 0.5   # 50% pressure -> PREEMPTIVE
        self.pressure_threshold_aggressive = 0.8   # 80% pressure -> AGGRESSIVE
        self.pressure_threshold_critical = 0.9      # 90% pressure -> AGGRESSIVE + FREEZE
        
        # State tracking
        self.last_strategy: Optional[GCStrategy] = None
        self.consecutive_high_pressure = 0
        self._preemptive_sweeps = 0
    
    def evaluate(self) -> GCStrategy:
        """Evaluate current memory pressure and return appropriate strategy.
        
        Returns:
            GCStrategy: The recommended GC strategy based on current conditions.
        """
        # Check cgroup critical state first (highest priority)
        cgroup_critical = self.sensors.is_cgroup_critical()
        if cgroup_critical is True:
            logger.warning("Cgroup critical state detected - triggering AGGRESSIVE GC")
            return GCStrategy.AGGRESSIVE
        
        # Read PSI pressure
        psi_data = self.sensors.read_psi()
        if psi_data is None:
            # Sensors unavailable - use SILENT to avoid unnecessary GC
            logger.debug("PSI sensors unavailable - using SILENT strategy")
            return GCStrategy.SILENT
        
        some_pressure, full_pressure, psi_critical = psi_data
        
        # Use the higher of some/full pressure
        current_pressure = max(some_pressure, full_pressure)
        
        # Critical pressure threshold
        if current_pressure >= self.pressure_threshold_critical or psi_critical:
            logger.warning(f"Critical pressure detected ({current_pressure:.2%}) - FREEZE")
            self.consecutive_high_pressure += 1
            return GCStrategy.FREEZE
        
        # Aggressive threshold
        if current_pressure >= self.pressure_threshold_aggressive:
            logger.info(f"High pressure detected ({current_pressure:.2%}) - AGGRESSIVE GC")
            self.consecutive_high_pressure += 1
            return GCStrategy.AGGRESSIVE
        
        # Preemptive threshold
        if current_pressure >= self.pressure_threshold_preemptive:
            logger.debug(f"Moderate pressure detected ({current_pressure:.2%}) - PREEMPTIVE GC")
            self.consecutive_high_pressure = max(0, self.consecutive_high_pressure - 1)
            return GCStrategy.PREEMPTIVE
        
        # Low pressure - SILENT
        self.consecutive_high_pressure = 0
        return GCStrategy.SILENT
    
    def apply_strategy(self, strategy: GCStrategy) -> int:
        """Apply a GC strategy by calling the runtime adapter.
        
        Args:
            strategy: The GC strategy to apply.
        
        Returns:
            int: Number of objects freed (if applicable).
        """
        self.last_strategy = strategy
        
        if strategy == GCStrategy.SILENT:
            # No action - prioritize CPU throughput
            return 0
        
        elif strategy == GCStrategy.PREEMPTIVE:
            # Clear short-lived objects (Gen 0 and 1)
            freed_0 = self.runtime.trigger_gc(0)
            freed_1 = self.runtime.trigger_gc(1)
            
            # Anti-tenuring counter: Prevent Gen 2 bloat by forcing a Gen 2 sweep 
            # every 5 preemptive hits, because manual Gen 0/1 sweeps break Native Gen 2 thresholds
            self._preemptive_sweeps += 1
            if self._preemptive_sweeps >= 5:
                 freed_2 = self.runtime.trigger_gc(2)
                 logger.debug(f"PREEMPTIVE GC (Scaled Full): freed {freed_0 + freed_1 + freed_2} objects (G0: {freed_0}, G1: {freed_1}, G2: {freed_2})")
                 self._preemptive_sweeps = 0
                 return freed_0 + freed_1 + freed_2
                 
            logger.debug(f"PREEMPTIVE GC: freed {freed_0 + freed_1} objects (Gen 0: {freed_0}, Gen 1: {freed_1})")
            return freed_0 + freed_1
        
        elif strategy == GCStrategy.AGGRESSIVE:
            # Full GC (Gen 2)
            freed = self.runtime.trigger_gc(2)
            logger.info(f"AGGRESSIVE GC: freed {freed} objects")
            return freed
        
        elif strategy == GCStrategy.FREEZE:
            # Freeze current objects as immortal
            self.runtime.apply_freeze()
            logger.info("FREEZE: Applied immortal branding to current objects")
            return 0
        
        return 0
    
    def tick(self) -> int:
        """Evaluate current conditions and apply appropriate strategy.
        
        This is the main entry point for periodic Governor execution.
        
        Returns:
            int: Number of objects freed by GC (if any).
        """
        strategy = self.evaluate()
        return self.apply_strategy(strategy)
    
    def get_last_strategy(self) -> Optional[GCStrategy]:
        """Get the last strategy that was applied.
        
        Returns:
            GCStrategy or None if no strategy has been applied yet.
        """
        return self.last_strategy
