from datetime import datetime, timezone

from fastapi import FastAPI


app = FastAPI(
    title="Healthcare Revenue Cycle API",
    version="0.1.0",
    description="MVP metadata and health endpoints for the local healthcare revenue cycle platform.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "hc-rcm-fhir-platform-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
