from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.api.dependencies import get_evaluation_runner
from app.api.jobs import Job, job_manager
from app.evaluation.runner import EvaluationRunner, parse_evaluation_report
from app.models.schemas import EvaluateRequest, EvaluationResultsResponse, JobStatus

router = APIRouter(tags=["evaluation"])


async def _run_job(job: Job, request: EvaluateRequest, runner: EvaluationRunner) -> None:
    await job_manager.update(job.job_id, status="running", progress=10, message="Building evaluation cases")
    try:
        report = await runner.run(job.job_id, request.judge, request.test_file)
        await job_manager.update(
            job.job_id,
            status="completed",
            progress=100,
            message="Evaluation completed",
            completed_at=datetime.now(timezone.utc),
            report_path=str(report),
        )
    except Exception as exc:
        await job_manager.update(
            job.job_id,
            status="failed",
            progress=100,
            message="Evaluation failed",
            completed_at=datetime.now(timezone.utc),
            error=str(exc),
        )


@router.post("/evaluate", response_model=JobStatus, status_code=202)
async def start_evaluation(
    request: EvaluateRequest,
    background_tasks: BackgroundTasks,
    runner: EvaluationRunner = Depends(get_evaluation_runner),
):
    if request.test_file and not request.test_file.startswith("data/"):
        raise HTTPException(status_code=400, detail="test_file must be under data/")
    job = await job_manager.create()
    background_tasks.add_task(_run_job, job, request, runner)
    return JobStatus(job_id=job.job_id, status=job.status, created_at=job.created_at)


@router.get("/evaluate/{job_id}", response_model=JobStatus)
async def evaluation_status(job_id: str):
    job = await job_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Evaluation job not found")
    return JobStatus(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        created_at=job.created_at,
        completed_at=job.completed_at,
        report_path=job.report_path,
        error=job.error,
    )


@router.get("/evaluate/{job_id}/results", response_model=EvaluationResultsResponse)
async def evaluation_results(job_id: str):
    job = await job_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Evaluation job not found")
    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Evaluation job is not completed (current status: {job.status})",
        )
    if not job.report_path or not Path(job.report_path).exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    data = await asyncio.to_thread(parse_evaluation_report, Path(job.report_path), job_id)
    if job.completed_at:
        data["completed_at"] = job.completed_at
    return EvaluationResultsResponse(**data)
