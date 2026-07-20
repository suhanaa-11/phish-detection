from fastapi import FastAPI
from pydantic import BaseModel

from ml.features.pipeline import build_feature_row
from ml.explain import explain_prediction

app = FastAPI(title="PhishGuard API", version="0.1.0")


class ScanRequest(BaseModel):
    url: str


@app.get("/")
def health_check():
    return {"status": "ok", "service": "PhishGuard API"}


@app.post("/scan")
def scan_url(request: ScanRequest):
    features = build_feature_row(request.url)
    result = explain_prediction(features)
    return {
        "url": request.url,
        "score": result["score"],
        "verdict": result["verdict"],
        "top_reasons": result["top_reasons"],
    }