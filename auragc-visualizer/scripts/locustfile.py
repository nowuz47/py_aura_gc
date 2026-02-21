"""Locust load testing scenarios for AuraGC."""

import os
from locust import HttpUser, task, between
import random

BASELINE_URL = os.environ.get("BASELINE_URL", "http://baseline:8000")
AURAGC_URL = os.environ.get("AURAGC_URL", "http://auragc:8000")


class SymmetricLoadUser(HttpUser):
    """User that sends exactly identical load to both Baseline and AuraGC simultaneously."""
    
    wait_time = between(0.5, 2.0)
    
    @task(3)
    def allocate_cyclic(self):
        """Primary task: create cyclic references (memory leak scenario)."""
        count = random.randint(500, 2000)
        # Send to both
        self.client.post(f"{BASELINE_URL}/allocate/cyclic?count={count}", name="Baseline: Cyclic Leak")
        self.client.post(f"{AURAGC_URL}/allocate/cyclic?count={count}", name="AuraGC: Cyclic Leak")
    
    @task(3)
    def allocate_ephemeral(self):
        """Secondary task: create ephemeral objects."""
        count = random.randint(5000, 15000)
        # Send to both
        self.client.post(f"{BASELINE_URL}/allocate/ephemeral?count={count}", name="Baseline: Ephemeral")
        self.client.post(f"{AURAGC_URL}/allocate/ephemeral?count={count}", name="AuraGC: Ephemeral")

    @task(1)
    def allocate_static(self):
        """Allocate static data (lookup tables)."""
        size_mb = random.randint(2, 10)
        self.client.post(f"{BASELINE_URL}/allocate/static?size_mb={size_mb}", name="Baseline: Static")
        self.client.post(f"{AURAGC_URL}/allocate/static?size_mb={size_mb}", name="AuraGC: Static")

    @task(1)
    def check_stats(self):
        """Periodic stats check."""
        self.client.get(f"{BASELINE_URL}/stats", name="Baseline: Stats")
        self.client.get(f"{AURAGC_URL}/stats", name="AuraGC: Stats")
