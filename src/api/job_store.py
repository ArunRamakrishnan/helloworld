"""In-memory async job store for long-running scan jobs.

Jobs are stored in a process-local dict. Suitable for single-process deployments.

TODO: Replace with Redis-backed store for multi-worker / distributed deployments.
"""
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

_jobs: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()

# Keep at most this many completed jobs in memory
MAX_JOBS = 50


def create_job(job_type: str = "universe_scan", params: Optional[Dict] = None) -> str:
    """Create a new job entry and return its ID."""
    job_id = str(uuid.uuid4())
    with _lock:
        # Evict oldest completed jobs if over limit
        completed = [jid for jid, j in _jobs.items() if j["status"] in ("complete", "failed")]
        if len(_jobs) >= MAX_JOBS and completed:
            oldest = sorted(completed, key=lambda jid: _jobs[jid]["created_at"])[:5]
            for jid in oldest:
                del _jobs[jid]

        _jobs[job_id] = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "started_at": None,
            "completed_at": None,
            "params": params or {},
            "progress": {"stage": "queued", "done": 0, "total": 0, "message": "Job queued"},
            "result": None,
            "error": None,
        }
    return job_id


def start_job(job_id: str):
    """Mark a job as running."""
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["status"] = "running"
            _jobs[job_id]["started_at"] = datetime.utcnow().isoformat() + "Z"


def update_progress(job_id: str, stage: str, done: int, total: int, message: str = ""):
    """Update job progress (called from background thread)."""
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["progress"] = {
                "stage": stage,
                "done": done,
                "total": total,
                "message": message,
                "pct": round(done / total * 100) if total > 0 else 0,
            }


def complete_job(job_id: str, result: Any):
    """Mark a job as complete with its result."""
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["status"] = "complete"
            _jobs[job_id]["completed_at"] = datetime.utcnow().isoformat() + "Z"
            _jobs[job_id]["result"] = result
            _jobs[job_id]["progress"]["message"] = "Complete"
            _jobs[job_id]["progress"]["pct"] = 100


def fail_job(job_id: str, error: str):
    """Mark a job as failed."""
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["completed_at"] = datetime.utcnow().isoformat() + "Z"
            _jobs[job_id]["error"] = error
            _jobs[job_id]["progress"]["message"] = f"Failed: {error}"


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a job by ID. Returns None if not found."""
    with _lock:
        job = _jobs.get(job_id)
        if job:
            return dict(job)  # return a copy
    return None


def list_jobs(limit: int = 20) -> list:
    """List recent jobs (newest first), without the full result payload."""
    with _lock:
        jobs = sorted(_jobs.values(), key=lambda j: j["created_at"], reverse=True)[:limit]
        return [
            {
                "job_id": j["job_id"],
                "job_type": j["job_type"],
                "status": j["status"],
                "created_at": j["created_at"],
                "completed_at": j.get("completed_at"),
                "progress": j["progress"],
                "error": j.get("error"),
            }
            for j in jobs
        ]
