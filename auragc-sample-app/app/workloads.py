"""Workload simulation logic for testing memory patterns."""

import gc
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class WorkloadSimulator:
    """Simulates different memory allocation patterns for testing."""
    
    def __init__(self):
        """Initialize the workload simulator."""
        self._ephemeral_objects: List[Any] = []
        self._cyclic_objects: List[Dict[str, Any]] = []
        self._static_objects: Dict[str, Any] = {}
    
    def allocate_ephemeral(self, count: int = 10000) -> Dict[str, int]:
        """Create many short-lived objects (simulates high-frequency API objects).
        
        Args:
            count: Number of objects to create.
        
        Returns:
            dict: Statistics about the allocation.
        """
        objects = []
        for i in range(count):
            # Create various ephemeral objects
            obj = {
                "id": i,
                "data": f"ephemeral_{i}" * 10,  # Small string
                "timestamp": i * 0.001,
            }
            objects.append(obj)
        
        # Keep reference to prevent immediate GC (simulating in-use objects)
        self._ephemeral_objects.extend(objects)
        
        # Periodically clear old ephemeral objects (simulating natural lifecycle)
        if len(self._ephemeral_objects) > count * 2:
            self._ephemeral_objects = self._ephemeral_objects[-count:]
        
        logger.info(f"Allocated {count} ephemeral objects")
        return {
            "allocated": count,
            "total_ephemeral": len(self._ephemeral_objects),
        }
    
    def allocate_cyclic(self, count: int = 1000) -> Dict[str, int]:
        """Create objects with circular references (simulates memory leaks).
        
        This creates objects that form cycles, which reference counting alone
        cannot free. Requires GC to detect and collect.
        
        Args:
            count: Number of cyclic object groups to create.
        
        Returns:
            dict: Statistics about the allocation.
        """
        cycles = []
        for i in range(count):
            # Create a cycle: A -> B -> C -> A
            a = {"id": i, "type": "node_a", "ref": None}
            b = {"id": i, "type": "node_b", "ref": None}
            c = {"id": i, "type": "node_c", "ref": None}
            
            a["ref"] = b
            b["ref"] = c
            c["ref"] = a
            
            # Add some data to increase memory footprint
            a["data"] = f"cyclic_data_{i}" * 100
            b["data"] = f"cyclic_data_{i}" * 100
            c["data"] = f"cyclic_data_{i}" * 100
            
            cycles.append({"a": a, "b": b, "c": c})
        
        # Keep reference to prevent GC (simulating leak)
        self._cyclic_objects.extend(cycles)
        
        logger.warning(f"Allocated {count} cyclic object groups (potential leak)")
        return {
            "allocated": count,
            "total_cyclic": len(self._cyclic_objects),
        }
    
    def allocate_static(self, size_mb: int = 10) -> Dict[str, int]:
        """Pre-load large lookup tables (simulates objects that should be frozen).
        
        Args:
            size_mb: Approximate size in MB to allocate.
        
        Returns:
            dict: Statistics about the allocation.
        """
        # Approximate: each entry ~100 bytes, so ~10k entries per MB
        entries_per_mb = 10000
        num_entries = size_mb * entries_per_mb
        
        lookup_table = {}
        for i in range(num_entries):
            key = f"static_key_{i}"
            value = {
                "id": i,
                "data": f"static_value_{i}" * 5,
                "metadata": {"index": i, "category": i % 10},
            }
            lookup_table[key] = value
        
        self._static_objects.update(lookup_table)
        
        logger.info(f"Allocated ~{size_mb}MB of static lookup data ({num_entries} entries)")
        return {
            "allocated_entries": num_entries,
            "total_static_entries": len(self._static_objects),
            "estimated_mb": size_mb,
        }
    
    def clear_ephemeral(self):
        """Clear ephemeral objects."""
        count = len(self._ephemeral_objects)
        self._ephemeral_objects.clear()
        logger.info(f"Cleared {count} ephemeral objects")
    
    def clear_cyclic(self):
        """Clear cyclic objects (triggers GC to break cycles)."""
        count = len(self._cyclic_objects)
        self._cyclic_objects.clear()
        gc.collect()  # Force collection to break cycles
        logger.info(f"Cleared {count} cyclic object groups")
    
    def get_stats(self) -> Dict[str, int]:
        """Get current workload statistics.
        
        Returns:
            dict: Statistics about current allocations.
        """
        return {
            "ephemeral_count": len(self._ephemeral_objects),
            "cyclic_count": len(self._cyclic_objects),
            "static_entries": len(self._static_objects),
        }
