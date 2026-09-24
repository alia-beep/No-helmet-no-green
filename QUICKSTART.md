# Quick Start Guide - No Helmet No Green Light

🚦 AI-powered traffic enforcement system with helmet detection

## ⚡ 5-Minute Quick Start

### 1️⃣ Prerequisites
```bash
# Ensure you have Python 3.8+ and PostgreSQL installed
python --version
psql --version
```

### 2️⃣ Setup
```bash
# Clone and activate environment
cd d:\no_green_no_light
python -m venv venv
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3️⃣ Database Setup
```bash
# Create PostgreSQL database
psql -U postgres
CREATE DATABASE traffic_ai;
CREATE USER traffic_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE traffic_ai TO traffic_user;
\q

# Load schema
psql -U traffic_user -d traffic_ai -f schema.sql
```

### 4️⃣ Configuration
Create `.env` file:
```env
DB_HOST=localhost
DB_USER=traffic_user
DB_PASSWORD=your_password
DB_NAME=traffic_ai
DB_PORT=5432

MODEL_PATH=AdvHelmet.pt
CONFIDENCE=0.25
FINE_AMOUNT=500
VIDEO_DIR=videos
OUTPUT_DIR=results
```

### 5️⃣ Run It
```bash
# Process videos
python main.py

# OR run dashboard
streamlit run dashboard.py

# OR start API
python -m uvicorn api:app --port 8000
```

---

## 📁 Directory Structure

| Directory | Purpose |
|-----------|---------|
| `videos/` | Place MP4 videos here |
| `results/` | Output detection CSVs and videos |
| `evaluation/` | Ground truth labels for accuracy |
| `dataset/` | Training/validation data |

---

## 🎯 Three Ways to Use

### 🎬 Batch Processing
```bash
python main.py
# Processes all videos in videos/ folder
# Outputs: results/video_name_detections.csv
```

### 🌐 REST API
```bash
python -m uvicorn api:app --port 8000

# Upload video:
curl -X POST -F "file=@video.mp4" http://localhost:8000/jobs

# Check status:
curl http://localhost:8000/jobs/{job_id}
```

### 📊 Interactive Dashboard
```bash
streamlit run dashboard.py
# Opens at http://localhost:8501
# View statistics, export reports
```

---

## 🛠️ Common Issues

| Issue | Solution |
|-------|----------|
| `Database connection refused` | Start PostgreSQL, check `.env` credentials |
| `AdvHelmet.pt not found` | Download from Ultralytics or place model in root |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| `Port 8000 already in use` | Use `--port 8001` instead |

---

## 📊 Evaluate Accuracy

```bash
# Edit ground truth file
# evaluation/ground_truth.csv

# Run evaluation
python evaluate_accuracy.py

# View results
python quick_accuracy.py
```

---

## 📁 Output Files

After processing, check `results/`:
```
video_1_detections.csv      → Detection records
video_1_detected.mp4        → Annotated video
audit.log                   → Processing logs
```

**Detection CSV columns:**
```
frame, timestamp, class, confidence, track_id, x1, y1, x2, y2
```

---

## 🔐 Important Notes

✅ **Educational prototype only**
✅ **E-challans are simulated** (no real fines)
✅ **Face blurring for privacy protection**
✅ **Optional: SMS & OCR features** (requires setup)

---

## 📚 Learn More

- **Full Docs**: See `README_COMPREHENSIVE.md`
- **API Docs**: Run API then visit `http://localhost:8000/docs`
- **YOLOv8**: https://docs.ultralytics.com/
- **FastAPI**: https://fastapi.tiangolo.com/

---

**Happy detecting!** 🚦
