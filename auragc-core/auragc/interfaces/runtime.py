"""RuntimeInterface - The outbound port for runtime adapters.

This is the abstract contract that runtime adapters (e.g., Python314Adapter)
must implement to bridge AuraGC Core's decision engine to the target runtime.
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple


class RuntimeInterface(ABC):
    """Abstract interface for runtime adapters.
    
    This port defines the contract that any runtime adapter must implement
    to enable AuraGC Core to interact with a garbage-collected runtime.
    """

    @abstractmethod
    def get_heap_usage(self) -> Dict[str, int]:
        """Retrieves current memory metrics from the target runtime.
        
        Returns:
            dict: A dictionary containing:
                - 'allocated_blocks': int - Number of allocated memory blocks
                - 'gen_counts': tuple - Generation counts (gen0, gen1, gen2)
        """
        pass

    @abstractmethod
    def trigger_gc(self, generation: int) -> int:
        """Triggers collection for the specified generation.
        
        Args:
            generation: The generation to collect (0, 1, or 2).
                        Generation 2 typically represents a full GC.
        
        Returns:
            int: Number of objects freed by this collection.
        """
        pass

    @abstractmethod
    def apply_freeze(self):
        """Signals the runtime to brand current objects as immortal.
        
        This operation freezes the current object graph, marking objects
        as permanent to reduce future GC scan overhead. Useful for
        long-lived lookup tables and static data structures.
        """
        pass
