"""Setup script for auragc-core."""

from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
import os
import sys
import platform

# Check if we're on Linux (required for PSI/cgroup)
IS_LINUX = platform.system() == "Linux"

# Define the C extension
native_extension = Extension(
    "auragc_native",
    sources=[
        "src/native_psi.c",
        "src/native_cgroup.c",
    ],
    include_dirs=["src"],
    extra_compile_args=["-std=c11", "-Wall", "-Wextra"] if IS_LINUX else [],
    extra_link_args=[],
)

# Only build native extension on Linux
ext_modules = [native_extension] if IS_LINUX else []


class BuildExt(build_ext):
    """Custom build extension to handle non-Linux platforms gracefully."""
    
    def build_extensions(self):
        if not IS_LINUX:
            print("Warning: Native sensors require Linux. Building Python-only package.")
            return
        
        # Set compiler flags
        for ext in self.extensions:
            ext.define_macros = [("AURAGC_BUILD", "1")]
        
        super().build_extensions()


setup(
    name="auragc-core",
    version="0.1.0",
    description="High-performance garbage collection orchestrator core",
    author="AuraGC Team",
    packages=find_packages(),
    ext_modules=ext_modules,
    cmdclass={"build_ext": BuildExt},
    python_requires=">=3.12",
    install_requires=[],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: C",
        "Operating System :: POSIX :: Linux",
    ],
)
