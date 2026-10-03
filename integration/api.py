"""Unified FastAPI endpoint for PHISHGUARD-X email analysis."""

from fastapi import FastAPI, HTTPException, Request

from .orchestrator import analyze_email_bytes
from .evidence_api import router as evidence_router

app = FastAPI(
    title="PHISHGUARD-X Email Analysis API",
    version="1.0.0",
)

app.include_router(evidence_router)


@app.get("/health")
def health_check():
    nlp_status = "unavailable"
    try:
        from nlp.distilbert import MODEL_DIR
        nlp_status = "ready" if MODEL_DIR.exists() else "model_missing"
    except Exception:
        pass
    return {"status": "ok", "nlp": nlp_status}



@app.post("/analyze-email")
async def analyze_email_endpoint(request: Request):
    raw_email = await request.body()
    if not raw_email:
        raise HTTPException(status_code=400, detail="Email content is empty")

    try:
        return analyze_email_bytes(raw_email)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Email analysis failed: {error}")
