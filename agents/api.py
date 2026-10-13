"""
FastAPI REST API Server for Q Fever Serology Classifier.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor
from serology_interpreter import SerologyInputError, interpret_serology

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Q Fever Serology Classifier API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


class SerologyRequest(BaseModel):
    phase_i_igg: str | int
    phase_ii_igg: str | int
    prior_phase_ii_igg: str | int | None = None
    persistent_focus: bool = False


@app.post("/api/serology/interpret")
def api_interpret(request: SerologyRequest):
    """IFA IgG interpretation only; no clinical diagnosis or patient identifiers."""
    try:
        return interpret_serology(
            request.phase_i_igg,
            request.phase_ii_igg,
            request.prior_phase_ii_igg,
            request.persistent_focus,
        )
    except SerologyInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "q-fever-serology-classifier", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
        return dossier.to_dict()
    except SecurityException as e:
        raise HTTPException(status_code=400, detail=f"Security violation: {str(e)}")


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException as e:
        raise HTTPException(status_code=400, detail=f"Security violation: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
