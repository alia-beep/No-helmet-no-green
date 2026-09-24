# API Reference Guide

## No Helmet No Green Light - REST API

FastAPI-based API for video processing and violation detection.

---

## Starting the API

```bash
# Start server
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000

# With specific host/port
python -m uvicorn api:app --host 127.0.0.1 --port 8001

# With workers for production
python -m uvicorn api:app --workers 4 --host 0.0.0.0 --port 8000
```

Access interactive docs at: **http://localhost:8000/docs**

---

## Endpoints

### 1. Health Check
**Check if API is running**

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "traffic-ai"
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8000/health
```

---

### 2. Create Job (Upload Video)
**Submit a video for processing**

```http
POST /jobs
Content-Type: multipart/form-data
```

**Parameters:**
- `file` (required): Video file (MP4, AVI, MOV, MKV)
  - Max size: depends on disk space
  - Supported formats: MP4, AVI, MOV, MKV

**Response (202 Accepted):**
```json
{
  "job_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "status": "queued",
  "filename": "traffic_video.mp4",
  "created_at": "2024-01-15T10:30:00.123456"
}
```

**cURL Example:**
```bash
curl -X POST \
  -F "file=@traffic_video.mp4" \
  http://localhost:8000/jobs
```

**Python Example:**
```python
import requests

with open('video.mp4', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/jobs', files=files)
    print(response.json())
```

**JavaScript/Node.js Example:**
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const data = new FormData();
data.append('file', fs.createReadStream('video.mp4'));

axios.post('http://localhost:8000/jobs', data, {
  headers: data.getHeaders()
}).then(res => console.log(res.data));
```

---

### 3. Get Job Status
**Check processing status of a video**

```http
GET /jobs/{job_id}
```

**Parameters:**
- `job_id` (path): Unique job identifier from upload response

**Response:**

*When queued/processing:*
```json
{
  "job_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "status": "processing",
  "filename": "traffic_video.mp4",
  "created_at": "2024-01-15T10:30:00.123456",
  "finished_at": null,
  "error": null
}
```

*When completed:*
```json
{
  "job_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "status": "completed",
  "filename": "traffic_video.mp4",
  "created_at": "2024-01-15T10:30:00.123456",
  "finished_at": "2024-01-15T10:35:00.654321",
  "error": null
}
```

*When failed:*
```json
{
  "job_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "status": "failed",
  "filename": "traffic_video.mp4",
  "created_at": "2024-01-15T10:30:00.123456",
  "finished_at": "2024-01-15T10:35:00.654321",
  "error": "Video format not supported"
}
```

**Status Values:**
- `queued` - Waiting to be processed
- `processing` - Currently being analyzed
- `completed` - Done successfully
- `failed` - Processing failed (check error field)

**cURL Example:**
```bash
curl http://localhost:8000/jobs/a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

**Polling Pattern (Python):**
```python
import time
import requests

job_id = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
base_url = "http://localhost:8000"

while True:
    response = requests.get(f"{base_url}/jobs/{job_id}")
    job = response.json()
    
    print(f"Status: {job['status']}")
    
    if job['status'] == 'completed':
        print("Job finished!")
        break
    elif job['status'] == 'failed':
        print(f"Error: {job['error']}")
        break
    
    time.sleep(5)  # Check every 5 seconds
```

---

### 4. Get Job Result
**Download detection results (CSV)**

```http
GET /jobs/{job_id}/result
```

**Parameters:**
- `job_id` (path): Unique job identifier

**Response:**
- Content-Type: `text/csv`
- Body: CSV file with detection records

**CSV Columns:**
```
frame,timestamp,class,confidence,track_id,x1,y1,x2,y2
1,0.0,helmet,0.95,1,100,150,200,250
2,0.033,no_helmet,0.87,2,250,200,350,350
3,0.067,helmet,0.92,1,102,152,202,252
```

**cURL Example:**
```bash
curl http://localhost:8000/jobs/{job_id}/result > detections.csv
```

**Python Example:**
```python
import requests
import csv

job_id = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
response = requests.get(f"http://localhost:8000/jobs/{job_id}/result")

# Save CSV
with open('detections.csv', 'w') as f:
    f.write(response.text)

# Parse CSV
reader = csv.DictReader(response.text.splitlines())
for row in reader:
    print(row)
```

---

## Error Responses

### 400 - Bad Request
```json
{
  "detail": "Only video files are supported"
}
```

**Causes:**
- Invalid file format (not MP4/AVI/MOV/MKV)
- Missing file in request
- Corrupted file

### 404 - Not Found
```json
{
  "detail": "Job not found"
}
```

**Causes:**
- Invalid job_id
- Job expired/deleted

### 500 - Server Error
```json
{
  "detail": "Internal server error"
}
```

**Causes:**
- Model loading failure
- Database connection error
- Processing exception

---

## Complete Example Workflow

### Step 1: Upload Video
```bash
JOB_ID=$(curl -s -X POST -F "file=@video.mp4" \
  http://localhost:8000/jobs | jq -r '.job_id')

echo "Job ID: $JOB_ID"
```

### Step 2: Poll for Completion
```bash
while true; do
  STATUS=$(curl -s http://localhost:8000/jobs/$JOB_ID | jq -r '.status')
  echo "Status: $STATUS"
  
  if [ "$STATUS" = "completed" ]; then
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Job failed!"
    exit 1
  fi
  
  sleep 5
done
```

### Step 3: Download Results
```bash
curl http://localhost:8000/jobs/$JOB_ID/result > detections.csv
echo "Results saved to detections.csv"
```

---

## Performance Considerations

**Processing Time:**
- 1 minute video: ~2-5 minutes (depends on video resolution, GPU)
- 10 minute video: ~20-50 minutes
- With GPU: 2-3x faster than CPU

**Memory Usage:**
- Model loading: ~2GB VRAM (GPU) / ~500MB RAM (CPU)
- Per-frame processing: ~200-500MB

**Best Practices:**
1. Use GPU for faster processing
2. Process videos in sequence via API
3. Compress videos before uploading (H.264 codec)
4. Monitor server resources with `top`/Task Manager

---

## Configuration

**API Settings (in `.env`):**
```env
API_HOST=0.0.0.0          # Listen on all interfaces
API_PORT=8000             # Port number
API_UPLOAD_DIR=api_data/uploads   # Upload directory
MODEL_PATH=AdvHelmet.pt   # Model file
CONFIDENCE=0.25           # Detection threshold
OUTPUT_DIR=results        # Results output
```

---

## Swagger UI

Interactive API documentation available at:
```
http://localhost:8000/docs
```

**Features:**
- Try-it-out button for each endpoint
- Request/response examples
- Parameter validation
- Auto-generated from FastAPI

---

## Rate Limiting

Currently no rate limiting. For production:
```python
# Add to api.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/jobs")
@limiter.limit("5/minute")  # 5 uploads per minute per IP
async def create_job(...):
    ...
```

---

## Deployment

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0"]
```

```bash
docker build -t traffic-ai .
docker run -p 8000:8000 -v $(pwd)/api_data:/app/api_data traffic-ai
```

### Production Server (Gunicorn + Uvicorn)
```bash
pip install gunicorn
gunicorn api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Troubleshooting

**API won't start:**
```bash
# Check port is available
lsof -i :8000

# Try different port
python -m uvicorn api:app --port 8001
```

**Jobs stuck in "processing":**
- Check `results/audit.log` for errors
- Restart API server
- Check disk space

**Upload fails:**
- Verify video format: `ffprobe video.mp4`
- Check file size (must fit in `api_data/uploads/`)
- Ensure read/write permissions

---

## Support

- API Docs: `http://localhost:8000/docs`
- Logs: `results/audit.log`
- Issues: Check project README troubleshooting section

