"""Locust load testing scenarios for AuraGC."""

from locust import HttpUser, task, between
import random


class LeakStormUser(HttpUser):
    """User that triggers memory leaks via cyclic allocations."""
    
    wait_time = between(0.5, 2.0)
    
    @task(3)
    def allocate_cyclic(self):
        """Primary task: create cyclic references (memory leak scenario)."""
        count = random.randint(500, 2000)
        self.client.post(f"/allocate/cyclic?count={count}")
    
    @task(1)
    def allocate_ephemeral(self):
        """Secondary task: create ephemeral objects."""
        count = random.randint(5000, 15000)
        self.client.post(f"/allocate/ephemeral?count={count}")
    
    @task(1)
    def check_stats(self):
        """Check current stats."""
        self.client.get("/stats")


class SpikeUser(HttpUser):
    """User that generates memory spikes."""
    
    wait_time = between(1.0, 3.0)
    
    @task(5)
    def allocate_ephemeral_burst(self):
        """Create bursts of ephemeral objects."""
        count = random.randint(10000, 50000)
        self.client.post(f"/allocate/ephemeral?count={count}")
    
    @task(1)
    def allocate_static(self):
        """Allocate static data."""
        size_mb = random.randint(5, 20)
        self.client.post(f"/allocate/static?size_mb={size_mb}")


class SteadyStateUser(HttpUser):
    """User that simulates steady background load."""
    
    wait_time = between(2.0, 5.0)
    
    @task(2)
    def allocate_ephemeral(self):
        """Steady ephemeral allocations."""
        count = random.randint(1000, 5000)
        self.client.post(f"/allocate/ephemeral?count={count}")
    
    @task(1)
    def check_stats(self):
        """Periodic stats check."""
        self.client.get("/stats")
