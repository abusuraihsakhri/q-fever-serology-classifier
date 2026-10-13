"""
Automated Pytest for Q Fever Serology Classifier REST API.
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set a test audit key before importing agents
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-secret-key-for-testing-only-32chars")

import pytest
from fastapi.testclient import TestClient
from agents.api import app


client = TestClient(app)


def test_health_endpoint():
    """Health endpoint should return HEALTHY status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["service"] == "q-fever-serology-classifier"


def test_metrics_endpoint():
    """Metrics endpoint should return operational metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "dossiers_processed_total" in data
    assert "audit_blocks_total" in data
    assert data["system_status"] == "NOMINAL_OPTIMAL"


def test_audit_endpoint():
    """Audit endpoint should process task and return dossier."""
    payload = {
        "task_id": "API-TEST-01",
        "target_identifier": "SPECIMEN-API-01",
        "primary_metric": 15.0,
        "secondary_metric": 5.0,
        "status_descriptor": "NOMINAL",
        "is_critical_flag": False,
    }
    response = client.post("/api/audit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "API-TEST-01"
    assert data["overall_urgency"] == "ROUTINE"
    assert data["audit_hash"] != ""


def test_audit_endpoint_critical():
    """Audit endpoint with critical flag should return CRITICAL urgency."""
    payload = {
        "task_id": "API-CRITICAL-01",
        "target_identifier": "SPECIMEN-CRITICAL",
        "primary_metric": 30.0,
        "secondary_metric": 15.0,
        "status_descriptor": "DISCORDANT_ANOMALY",
        "is_critical_flag": True,
    }
    response = client.post("/api/audit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_urgency"] == "CRITICAL_STAT_PANIC"
    assert data["critical_alerts_count"] > 0


def test_audit_endpoint_phi_blocked():
    """Audit endpoint with PHI in task_id should be rejected."""
    payload = {
        "task_id": "Patient MRN-12345678",
        "target_identifier": "SPECIMEN-01",
        "primary_metric": 10.0,
        "secondary_metric": 5.0,
        "status_descriptor": "NOMINAL",
        "is_critical_flag": False,
    }
    response = client.post("/api/audit", json=payload)
    assert response.status_code == 400


def test_chat_endpoint():
    """Chat endpoint should return a response."""
    response = client.post("/api/chat", json={"query": "What is the status?"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert len(data["response"]) > 0


def test_audit_logs_endpoint():
    """Audit logs endpoint should return trail with integrity status."""
    response = client.get("/api/audit/logs")
    assert response.status_code == 200
    data = response.json()
    assert "audit_trail" in data
    assert "verified" in data
    assert isinstance(data["verified"], bool)

def test_serology_interpret_api():
    response = client.post("/api/serology/interpret", json={
        "phase_i_igg": "1:64", "phase_ii_igg": "1:256",
        "prior_phase_ii_igg": "1:64", "persistent_focus": False
    })
    assert response.status_code == 200
    assert response.json()["status"] == "acute_seroconversion_pattern"


def test_serology_interpret_api_bad_titer():
    response = client.post("/api/serology/interpret", json={
        "phase_i_igg": "<1:16", "phase_ii_igg": 256
    })
    assert response.status_code == 422
