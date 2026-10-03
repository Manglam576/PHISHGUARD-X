from fastapi import FastAPI

app = FastAPI(
    title="ThreatGraph",
    description="Email Threat Intelligence and Infrastructure Correlation Platform"
)

@app.get("/")
def home():
    return {
        "message": "ThreatGraph is running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }