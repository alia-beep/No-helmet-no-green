# Points 6, 8 and 10 implemented

**6 Reporting / Analytics**
- `report_generator.py`: CSV and HTML summary reports.
- `dashboard.py`: compliance rate over time and report export.

**8 Privacy & Compliance**
- `privacy.py`: Gaussian-blur detected faces before storing output video.
- `retention.py`: configurable cleanup of old raw media.
- `main.py`: audit log in `results/audit.log`.

**10 API / Service Layer**
- `api.py`: FastAPI REST service.
- `POST /jobs`: upload and queue a video.
- `GET /jobs/{job_id}`: status.
- `GET /jobs/{job_id}/result`: result.
- `GET /health`: health check.

Run:
`uvicorn api:app --host 0.0.0.0 --port 8000`
