"""Python 3.14 Runtime Adapter - Implements RuntimeInterface for Python."""

import gc
import sys
import logging
import threading
from typing import Dict
from auragc.interfaces.runtime import RuntimeInterface

logger = logging.getLogger(__name__)


class Python314Adapter(RuntimeInterface):
    """Adapter that bridges AuraGC Core to Python 3.14's garbage collector."""
    
    def __init__(self):
        """Initialize the Python adapter."""
        self.lock = threading.Lock()
        logger.info("Python314Adapter initialized with re-entrancy protection")
    
    def get_heap_usage(self) -> Dict[str, int]:
        """Retrieve current memory metrics from Python runtime."""
        try:
            allocated_blocks = sys.getallocatedblocks()
        except AttributeError:
            allocated_blocks = 0
        
        gen_counts = gc.get_count()
        
        return {
            "allocated_blocks": allocated_blocks,
            "gen_counts": gen_counts,
        }
    
    def trigger_gc(self, generation: int) -> int:
        """Trigger garbage collection safely with Tier 3 improvements."""
        if generation not in (0, 1, 2):
            generation = 2
        
        with self.lock:
            try:
                # Tier 3: Pre-collection Cleanup
                # Clear volatile objects first to reduce Full GC overhead
                if generation == 2:
                    gc.collect(0)
                    logger.debug("Tier 3: Pre-cleanup (Gen 0) triggered before Full GC")

                # Get counts before collection
                before = sum(gc.get_count())
                
                # Trigger collection
                collected = gc.collect(generation)
                
                # Get counts after collection
                after = sum(gc.get_count())
                
                logger.debug(f"GC generation {generation}: collected {collected} objects, "
                            f"freed {before - after} objects")
                
                return collected
            except Exception as e:
                logger.error(f"Tier 3 Shield: GC trigger failed: {e}")
                return 0
    
    def apply_freeze(self):
        """Tier 3: Safely freeze current objects as immortal."""
        with self.lock:
            try:
                # First, do a full collection to clean up cycles
                gc.collect()
                
                # Freeze current objects
                try:
                    gc.freeze()
                    logger.info("Applied freeze: current objects marked as immortal")
                except AttributeError:
                    logger.warning("gc.freeze() not available in this Python version")
            except Exception as e:
                logger.error(f"Tier 3 Shield: Freeze failed: {e}")
