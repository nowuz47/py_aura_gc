"""Python wrapper for native C sensors (PSI and Cgroup).

This module provides a Python interface to the low-level C sensors
that monitor Linux PSI and cgroup v2 memory events.
"""

import ctypes
import os
import platform
from typing import Optional, Tuple
from ctypes import Structure, c_double, c_bool, c_int, c_uint64, POINTER

# Determine library extension based on platform
if platform.system() == "Linux":
    _lib_ext = ".so"
elif platform.system() == "Darwin":
    _lib_ext = ".dylib"
else:
    _lib_ext = ".dll"

# Try to load the compiled extension (will be built by setup.py)
_lib_path = os.path.join(os.path.dirname(__file__), "..", "..", "src", f"libauragc_native{_lib_ext}")
if not os.path.exists(_lib_path):
    # Fallback: try to find it in build directory
    _lib_path = None

# PSI Reading structure (matches C struct)
class PSIReading(Structure):
    _fields_ = [
        ("some_pressure", c_double),
        ("full_pressure", c_double),
        ("critical", c_bool),
    ]


class SensorError(Exception):
    """Raised when sensor operations fail."""
    pass


class NativeSensors:
    """Wrapper for native C sensor functions."""
    
    def __init__(self):
        """Initialize the native sensor library."""
        if _lib_path and os.path.exists(_lib_path):
            self._lib = ctypes.CDLL(_lib_path)
        else:
            # Stub implementation for non-Linux or when library not built
            self._lib = None
            if platform.system() != "Linux":
                return  # Graceful degradation on non-Linux
        
        if self._lib:
            # Setup function signatures
            self._lib.auragc_psi_read.argtypes = [POINTER(PSIReading)]
            self._lib.auragc_psi_read.restype = c_int
            
            self._lib.auragc_psi_check_pressure.argtypes = [POINTER(c_double)]
            self._lib.auragc_psi_check_pressure.restype = c_int
            
            self._lib.auragc_cgroup_is_critical.argtypes = [POINTER(c_bool)]
            self._lib.auragc_cgroup_is_critical.restype = c_int
    
    def read_psi(self) -> Optional[Tuple[float, float, bool]]:
        """Read current PSI pressure values.
        
        Returns:
            tuple: (some_pressure, full_pressure, critical) or None if unavailable.
                  Pressure values are 0.0-1.0 (normalized).
        """
        if not self._lib:
            return None
        
        reading = PSIReading()
        result = self._lib.auragc_psi_read(ctypes.byref(reading))
        
        if result != 0:
            return None
        
        return (reading.some_pressure, reading.full_pressure, reading.critical)
    
    def check_psi_pressure(self) -> Optional[float]:
        """Check if PSI pressure exceeds threshold.
        
        Returns:
            float: Current pressure (0.0-1.0) if available, None otherwise.
        """
        if not self._lib:
            return None
        
        pressure = c_double()
        result = self._lib.auragc_psi_check_pressure(ctypes.byref(pressure))
        
        if result < 0:
            return None
        
        return pressure.value
    
    def is_cgroup_critical(self) -> Optional[bool]:
        """Check if cgroup memory is in critical state.
        
        Returns:
            bool: True if critical (OOM or max threshold), False if not,
                  None if cgroup monitoring unavailable.
        """
        if not self._lib:
            return None
        
        critical = c_bool()
        result = self._lib.auragc_cgroup_is_critical(ctypes.byref(critical))
        
        if result != 0:
            return None
        
        return critical.value


# Global sensor instance
_sensors = None


def get_sensors() -> NativeSensors:
    """Get or create the global sensor instance."""
    global _sensors
    if _sensors is None:
        _sensors = NativeSensors()
    return _sensors
