from agents.base import AuditTrail


def test_hmac_detects_payload_metadata_tampering():
    trail = AuditTrail("sample-test-secret-key-with-over-32-chars")
    trail.log("worker", "staff", "RUN", {"status": "ok"})
    trail.log("worker", "staff", "NEXT", {"status": "ok"})
    assert trail.verify_integrity()
    trail.logs[0]["event_type"] = "EDITED"
    assert not trail.verify_integrity()


def test_get_trail_does_not_expose_mutable_internal_history():
    trail = AuditTrail("sample-test-secret-key-with-over-32-chars")
    trail.log("worker", "staff", "RUN", {"status": "ok"})
    trail.get_trail()[0]["event_type"] = "EDITED"
    assert trail.verify_integrity()
