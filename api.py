import os, uuid
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from ultralytics import YOLO
from main1 import process_video

load_dotenv()
app = FastAPI(title="No Helmet No Green Light API", version="1.0")
UPLOAD_DIR = Path(os.getenv("API_UPLOAD_DIR", "api_data/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
Path(os.getenv("OUTPUT_DIR", "results")).mkdir(parents=True, exist_ok=True)
JOBS = {}

def run_job(job_id, input_path):
    JOBS[job_id]["status"] = "processing"
    try:
        model = YOLO(os.getenv("MODEL_PATH", "AdvHelmet.pt"))
        result = process_video(Path(input_path), model, show_window=False)
        JOBS[job_id].update(status="completed", result=result, finished_at=datetime.now().isoformat())
    except Exception as exc:
        JOBS[job_id].update(status="failed", error=str(exc), finished_at=datetime.now().isoformat())

@app.get("/health")
def health():
    return {"status": "ok", "service": "traffic-ai"}

@app.post("/jobs", status_code=202)
async def create_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    suffix = Path(file.filename or "upload.mp4").suffix.lower()
    if suffix not in {".mp4", ".avi", ".mov", ".mkv"}:
        raise HTTPException(400, "Only video files are supported")
    job_id = uuid.uuid4().hex
    path = UPLOAD_DIR / (job_id + suffix)
    path.write_bytes(await file.read())
    JOBS[job_id] = {"status": "queued", "filename": file.filename,
                    "created_at": datetime.now().isoformat()}
    background_tasks.add_task(run_job, job_id, str(path))
    return {"job_id": job_id, "status_url": f"/jobs/{job_id}",
            "result_url": f"/jobs/{job_id}/result"}

@app.get("/jobs/{job_id}")
def job_status(job_id):
    if job_id not in JOBS:
        raise HTTPException(404, "Job not found")
    return JOBS[job_id]

@app.get("/jobs/{job_id}/result")
def job_result(job_id):
    if job_id not in JOBS:
        raise HTTPException(404, "Job not found")
    job = JOBS[job_id]
    if job["status"] != "completed":
        raise HTTPException(409, f"Job status: {job['status']}")
    result = job.get("result", {})
    path = result.get("output_video")
    if path and Path(path).exists():
        return FileResponse(path, media_type="video/mp4", filename=Path(path).name)
    return result
@app.post("/process")
async def process_video_direct(file: UploadFile = File(...)):

    suffix = Path(file.filename or "upload.mp4").suffix.lower()

    if suffix not in {".mp4", ".avi", ".mov", ".mkv"}:
        raise HTTPException(
            400,
            "Only video files are supported"
        )

    # Save uploaded video
    input_path = UPLOAD_DIR / (
        uuid.uuid4().hex + suffix
    )

    input_path.write_bytes(await file.read())

    try:

        # Load model
        model = YOLO(
            os.getenv(
                "MODEL_PATH",
                "AdvHelmet.pt"
            )
        )

        # Process video
        result = process_video(
            input_path,
            model,
            show_window=False
        )

        # Get output video
        output_video = result.get("output_video")

        if not output_video:
            return result

        if not Path(output_video).exists():
            raise HTTPException(
                500,
                "Output video was not created"
            )

        # Return processed video directly
        return FileResponse(
            output_video,
            media_type="video/mp4",
            filename=Path(output_video).name
        )

    except Exception as exc:

        raise HTTPException(
            500,
            f"Video processing failed: {str(exc)}"
        )
