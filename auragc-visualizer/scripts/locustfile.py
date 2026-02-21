"""Locust load testing scenarios for AuraGC."""

import os
from locust import HttpUser, task, between
import random

BASELINE_URL = os.environ.get("BASELINE_URL", "http://baseline:8000")
AURAGC_URL = os.environ.get("AURAGC_URL", "http://auragc:8000")


"""Locust load testing scenarios for AuraGC."""

import os
from locust import HttpUser, task, between, events
from flask import request, jsonify

BASELINE_URL = os.environ.get("BASELINE_URL", "http://baseline:8000")
AURAGC_URL = os.environ.get("AURAGC_URL", "http://auragc:8000")

class CustomState:
    mode = "leak_storm"  # leak_storm, jitter, throughput

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    if environment.web_ui:
        @environment.web_ui.app.route("/test_mode", methods=["POST", "GET"])
        def set_mode():
            if request.method == "POST":
                CustomState.mode = request.form.get("mode", "leak_storm")
            return jsonify({"mode": CustomState.mode})

class AuraGCTestUser(HttpUser):
    """User that sends exactly identical load to both Baseline and AuraGC simultaneously."""
    wait_time = between(0.1, 0.5)
    
    @task
    def execute_test(self):
        mode = CustomState.mode
        if mode == "leak_storm":
            # Test 1: Simulate memory leak via circular references
            self.client.post(f"{BASELINE_URL}/allocate/cyclic?count=500", name="Baseline: Cyclic Leak")
            self.client.post(f"{AURAGC_URL}/allocate/cyclic?count=500", name="AuraGC: Cyclic Leak")
        
        elif mode == "jitter":
            # Test 2: Stream of lightweight requests checking fast allocation efficiency 
            self.client.post(f"{BASELINE_URL}/allocate/ephemeral?count=2000", name="Baseline: Jitter Ping")
            self.client.post(f"{AURAGC_URL}/allocate/ephemeral?count=2000", name="AuraGC: Jitter Ping")
            
        elif mode == "throughput":
            # Test 3: Variable load requests, slightly heavier ephemeral traffic
            self.client.post(f"{BASELINE_URL}/allocate/ephemeral?count=10000", name="Baseline: Heavy Ping")
            self.client.post(f"{AURAGC_URL}/allocate/ephemeral?count=10000", name="AuraGC: Heavy Ping")
