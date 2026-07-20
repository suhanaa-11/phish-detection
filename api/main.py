from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.responses import HTMLResponse
from api.dashboard import DASHBOARD_HTML
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response

from ml.features.pipeline import build_feature_row
from ml.explain import explain_prediction
from ml.url_extractor import extract_urls_from_text
from api.database import init_db, log_scan, get_recent_scans, get_stats

app = FastAPI(title="PhishGuard API", version="0.3.0")
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

init_db()


class ScanRequest(BaseModel):
    url: str


class BatchScanRequest(BaseModel):
    urls: List[str] = []
    text: str = ""


def _scan_single(url: str) -> dict:
    features = build_feature_row(url)
    result = explain_prediction(features)
    log_scan(url, result["score"], result["verdict"])
    return {
        "url": url,
        "score": result["score"],
        "verdict": result["verdict"],
        "top_reasons": result["top_reasons"],
    }


@app.get("/")
def health_check():
    return {"status": "ok", "service": "PhishGuard API"}


@app.post("/scan")
@limiter.limit("20/minute")
def scan_url(request: Request, response: Response, scan_request: ScanRequest):
    return _scan_single(scan_request.url)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML

@app.post("/scan-batch")
@limiter.limit("10/minute")
def scan_batch(request: Request, response: Response, batch_request: BatchScanRequest):
    urls_to_scan = list(batch_request.urls)

    if request.text:
        found = extract_urls_from_text(batch_request.text)
        urls_to_scan.extend(found)

    seen = set()
    unique_urls = []
    for u in urls_to_scan:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)

    results = [_scan_single(u) for u in unique_urls]
    flagged_count = sum(1 for r in results if r["verdict"] == "phishing")

    return {
        "total_scanned": len(results),
        "flagged_count": flagged_count,
        "results": results,
    }


@app.get("/history")
def scan_history(limit: int = 50):
    return {
        "stats": get_stats(),
        "scans": get_recent_scans(limit),
    }