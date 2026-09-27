"""
DebugFlow — FastAPI backend entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import analyze, fix, run_tests, report

app = FastAPI(
    title="DebugFlow API",
    description="AI-assisted debugging workflow backend.",
    version="0.1.0",
)

# Allow the React dev server (localhost:5173 / 3000) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173","https://debug-flow-pi.vercel.app",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
app.include_router(fix.router, prefix="/fix", tags=["fix"])
app.include_router(run_tests.router, prefix="/run-tests", tags=["run-tests"])
app.include_router(report.router, prefix="/report", tags=["report"])


@app.get("/health", tags=["health"])
def health() -> dict:
    """Liveness check."""
    return {"status": "ok"}
