"""Python 3.14 Runtime Adapter - Implements RuntimeInterface for Python."""

import gc
import sys
import logging
from typing import Dict
from auragc.interfaces.runtime import RuntimeInterface

logger = logging.getLogger(__name__)


class Python314Adapter(RuntimeInterface):
    """Adapter that bridges AuraGC Core to Python 3.14's garbage collector.
    
    This adapter implements the RuntimeInterface port, allowing the Governor
    to control Python's GC via standard gc module APIs.
    """
    
    def __init__(self):
        """Initialize the Python adapter."""
        logger.info("Python314Adapter initialized")
    
    def get_heap_usage(self) -> Dict[str, int]:
        """Retrieve current memory metrics from Python runtime.
        
        Returns:
            dict: Dictionary containing:
                - 'allocated_blocks': Number of allocated memory blocks
                - 'gen_counts': Tuple of (gen0, gen1, gen2) counts
        """
        try:
            allocated_blocks = sys.getallocatedblocks()
        except AttributeError:
            # sys.getallocatedblocks() may not be available in all Python versions
            allocated_blocks = 0
        
        gen_counts = gc.get_count()
        
        return {
            "allocated_blocks": allocated_blocks,
            "gen_counts": gen_counts,
        }
    
    def trigger_gc(self, generation: int) -> int:
        """Trigger garbage collection for the specified generation.
        
        Args:
            generation: The generation to collect (0, 1, or 2).
                        Generation 2 typically represents a full GC.
        
        Returns:
            int: Number of objects freed by this collection.
        """
        if generation not in (0, 1, 2):
            logger.warning(f"Invalid generation {generation}, defaulting to 2")
            generation = 2
        
        # Get counts before collection
        before = sum(gc.get_count())
        
        # Trigger collection
        collected = gc.collect(generation)
        
        # Get counts after collection
        after = sum(gc.get_count())
        
        logger.debug(f"GC generation {generation}: collected {collected} objects, "
                    f"freed {before - after} objects")
        
        return collected
    
    def apply_freeze(self):
        """Freeze current objects as immortal to reduce future GC scan overhead.
        
        This marks all currently alive objects as permanent, preventing them
        from being scanned in future GC cycles. Useful for long-lived lookup
        tables and static data structures.
        """
        # First, do a full collection to clean up cycles
        gc.collect()
        
        # Freeze current objects
        try:
            gc.freeze()
            logger.info("Applied freeze: current objects marked as immortal")
        except AttributeError:
            # gc.freeze() requires Python 3.7+
            logger.warning("gc.freeze() not available in this Python version")
