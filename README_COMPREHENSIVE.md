# 🚦 No Helmet No Green Light

An intelligent AI-powered traffic enforcement system that detects helmet violations using computer vision, generates automated e-challans (traffic fines), and provides real-time analytics through an interactive dashboard.

**Note:** This is an educational prototype. E-challans and fines are simulated for demonstration purposes. No real money is deducted.

---

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Dashboard](#dashboard)
- [Accuracy Evaluation](#accuracy-evaluation)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

### Core Functionality
- **Real-time Helmet Detection**: Uses YOLOv8 AI model to detect violations in video feeds
- **Person Tracking**: ByteTrack algorithm for consistent person tracking across frames
- **Automated E-Challan Generation**: Creates violation records with unique challan numbers
- **Vehicle Number Detection**: Optional license plate/vehicle number extraction using EasyOCR
- **Face Privacy Protection**: Automatic face blurring in detected frames

### Data Management
- **PostgreSQL Integration**: Persistent storage of detection events and challans
- **Audit Logging**: Comprehensive logging of all violations and processing events
- **CSV Export**: Export detection results and challan records to CSV format
- **HTML Reports**: Generate visual traffic enforcement reports

### Analytics & Visualization
- **Interactive Streamlit Dashboard**: Real-time violation statistics and compliance metrics
- **Multiple Chart Types**: Bar charts, violation summaries, and trend analysis
- **Compliance Rate Calculation**: Monitor helmet compliance percentage
- **Video-wise Analytics**: Break down violations by video source

### API & Automation
- **RESTful API**: FastAPI-based API for video processing
- **Background Job Processing**: Asynchronous video processing without blocking
- **SMS Notifications**: Optional Twilio integration for real-time alerts
- **Batch Processing**: Process multiple videos sequentially

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **AI Model** | YOLOv8 (Ultralytics) |
| **Tracking** | ByteTrack |
| **Video Processing** | OpenCV (cv2) |
| **Backend API** | FastAPI |
| **Dashboard** | Streamlit |
| **Database** | PostgreSQL |
| **Data Analysis** | Pandas, NumPy, Scikit-learn |
| **Visualization** | Plotly |
| **OCR** | EasyOCR (optional) |
| **SMS** | Twilio (optional) |
| **Image Processing** | Pillow |
| **Python** | 3.8+ |

---

## 📁 Project Structure

```
no_green_no_light/
├── main.py                          # Main video processing pipeline
├── main1.py                         # Alternative processing script
├── api.py                           # FastAPI server for video uploads
├── dashboard.py                     # Streamlit analytics dashboard
├── db.py                            # PostgreSQL database operations
├── services.py                      # Business logic (challan generation, SMS)
├── privacy.py                       # Face blurring and privacy functions
│
├── 📊 Evaluation & Analysis
├── evaluate_accuracy.py             # Compare predictions with ground truth
├── evaluate_csv.py                  # CSV-based accuracy evaluation
├── quick_accuracy.py                # Quick accuracy check
├── val_accuracy.py                  # Validation dataset accuracy
├── evaluate_videos_original.py      # Original video evaluation
├── accuracy.py                      # Accuracy calculation utilities
├── actual_labels.py                 # Ground truth label management
├── report.py                        # Report generation (CSV, HTML)
├── test_report.py                   # Report testing
├── benchmark.py                     # Performance benchmarking
│
├── 📝 Data & Models
├── schema.sql                       # PostgreSQL database schema
├── requirements.txt                 # Python dependencies
├── requirements_enhanced.txt        # Extended dependencies list
├── AdvHelmet.pt                     # Pre-trained YOLOv8 model
├── .env                             # Environment variables (create this)
├── .env.example                     # Example environment configuration
│
├── 📁 Directories
├── dataset/                         # Training/validation dataset
│   ├── data.yaml                    # Dataset configuration
│   ├── images/                      # Image files (train/test/val splits)
│   └── labels/                      # YOLO format annotations
│
├── results/                         # Detection results
│   ├── video_*_detections.csv       # Per-video detection CSVs
│   └── *_detections.csv             # Processed video results
│
├── evaluation/                      # Evaluation artifacts
│   ├── ground_truth.csv             # Manual ground truth labels
│   ├── evaluation_results.csv       # Accuracy evaluation results
│   ├── confusion_matrix.csv         # Classification confusion matrix
│   └── frames/                      # Evaluation frame images
│
├── runs/                            # YOLO training/inference runs
│
├── videos/                          # Input video files (MP4, AVI, MOV, MKV)
│
├── reports/                         # Generated reports
│   └── traffic_summary.html         # HTML traffic report
│
├── api_data/
│   └── uploads/                     # API file uploads
│
└── README.md                        # Quick start guide
```

---

## 📦 Prerequisites

- **Python**: 3.8 or higher
- **PostgreSQL**: 12 or higher (database and user created)
- **GPU** (optional): CUDA-capable GPU for faster processing
- **Storage**: ~2GB for model and dataset

### System Requirements
- Windows/Linux/macOS
- 8GB RAM minimum (16GB recommended)
- SSD for faster video processing

---

## 🚀 Installation

### Step 1: Clone Repository and Setup Python Environment

```bash
# Navigate to project directory
cd d:\no_green_no_light

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\Activate.ps1

# Activate virtual environment (Linux/macOS)
source venv/bin/activate
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

For enhanced features (OCR, SMS, etc.):
```bash
pip install -r requirements_enhanced.txt
```

### Step 3: Setup PostgreSQL Database

1. **Create Database** (using pgAdmin or command line):
   ```sql
   CREATE DATABASE traffic_ai;
   CREATE USER traffic_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE traffic_ai TO traffic_user;
   ```

2. **Run Schema** (in pgAdmin or psql):
   ```bash
   # Using psql
   psql -U traffic_user -d traffic_ai -f schema.sql
   ```

### Step 4: Configure Environment Variables

Create `.env` file in project root:

```env
# Database Configuration
DATABASE_URL=postgresql://traffic_user:your_password@localhost:5432/traffic_ai
DB_HOST=localhost
DB_USER=traffic_user
DB_PASSWORD=your_password
DB_NAME=traffic_ai
DB_PORT=5432

# Model Configuration
MODEL_PATH=AdvHelmet.pt
CONFIDENCE=0.25              # Detection confidence threshold (0-1)
FINE_AMOUNT=500              # Simulated fine amount in currency units

# Video Processing
VIDEO_DIR=videos
OUTPUT_DIR=results
VIOLATION_COOLDOWN_SECONDS=10  # Minimum seconds between same-person violations

# API Configuration (optional)
API_UPLOAD_DIR=api_data/uploads
API_HOST=0.0.0.0
API_PORT=8000

# Twilio SMS (optional)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI/OCR (optional)
OPENAI_API_KEY=your_key
```

### Step 5: Obtain Pre-trained Model

1. Place `AdvHelmet.pt` in project root directory, OR
2. Download from Ultralytics model hub:
   ```bash
   python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
   ```

### Step 6: Test Database Connection

```bash
python test_db.py
```

Expected output:
```
✓ Database connection successful
✓ Schema verified
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PATH` | `AdvHelmet.pt` | Path to YOLOv8 model file |
| `CONFIDENCE` | `0.25` | Detection confidence threshold (0-1) |
| `FINE_AMOUNT` | `500` | Simulated fine amount |
| `VIOLATION_COOLDOWN_SECONDS` | `10` | Cooldown between violations for same person |
| `VIDEO_DIR` | `videos` | Input video directory |
| `OUTPUT_DIR` | `results` | Output results directory |
| `DATABASE_URL` | - | PostgreSQL connection string |

### Model Configuration

Edit model settings in `main.py`:
- **Confidence Threshold**: Controls detection sensitivity (0.25 = 25% confidence minimum)
- **Tracker**: ByteTrack (default) or DeepSORT
- **Frame Skip**: Process every Nth frame for performance

---

## 📺 Usage

### Option 1: Batch Video Processing

```bash
# Process all videos in 'videos/' directory
python main.py
```

**Process Flow:**
1. Loads YOLOv8 model from `AdvHelmet.pt`
2. Scans `videos/` directory for MP4/AVI/MOV/MKV files
3. For each frame:
   - Detects persons and helmets
   - Tracks detections across frames
   - Generates e-challans for violations
   - Saves detection results to CSV
4. Outputs:
   - `results/*_detections.csv` - Detection records
   - `results/*_detected.mp4` - Annotated video
   - `results/audit.log` - Processing log

### Option 2: REST API

**Start API Server:**
```bash
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/jobs` | POST | Upload and process video |
| `/jobs/{job_id}` | GET | Check job status |
| `/jobs/{job_id}/result` | GET | Download results |
| `/docs` | GET | Swagger API documentation |

**Upload Video via API:**
```bash
curl -X POST \
  -F "file=@video.mp4" \
  http://localhost:8000/jobs
```

**Response:**
```json
{
  "job_id": "a1b2c3d4e5f6g7h8",
  "status": "queued",
  "created_at": "2024-01-15T10:30:00",
  "filename": "video.mp4"
}
```

**Check Job Status:**
```bash
curl http://localhost:8000/jobs/a1b2c3d4e5f6g7h8
```

### Option 3: Interactive Dashboard

```bash
streamlit run dashboard.py
```

Opens browser at `http://localhost:8501`

**Dashboard Features:**
- Total challans issued
- Total fine amount
- RED signal violations count
- Helmet compliance rate
- E-challan records table (sortable, filterable)
- Violations per video chart
- Violation type breakdown
- Payment status summary
- Export options (CSV, HTML)

---

## 🔌 API Documentation

### Health Check
```bash
GET /health

Response: { "status": "ok", "service": "traffic-ai" }
```

### Upload Video for Processing
```bash
POST /jobs

Request:
  - multipart/form-data
  - file: [video file] (MP4, AVI, MOV, MKV)

Response (202 Accepted):
{
  "job_id": "uuid-string",
  "status": "queued",
  "filename": "video.mp4",
  "created_at": "2024-01-15T10:30:00.000Z"
}
```

### Get Job Status
```bash
GET /jobs/{job_id}

Response:
{
  "job_id": "uuid-string",
  "status": "processing|completed|failed",
  "filename": "video.mp4",
  "created_at": "2024-01-15T10:30:00.000Z",
  "finished_at": "2024-01-15T10:35:00.000Z",
  "error": null  // If failed: error message
}
```

### Get Job Result
```bash
GET /jobs/{job_id}/result

Response: CSV file with detection records
```

---

## 📊 Dashboard

### Available Metrics

**Summary Cards:**
- **Total Challans**: Count of all violations recorded
- **Total Fine**: Sum of all simulated fines
- **RED Violations**: Violations during red light (if signal_status tracked)
- **Compliance Rate**: Percentage of frames with helmet compliance

**Charts & Visualizations:**
- Violations by video (bar chart)
- Violation types (pie chart)
- Violations over time (line chart)
- Payment status breakdown

**Data Table:**
- Sortable/filterable e-challan records
- Columns: ID, Challan No, Timestamp, Video, Vehicle, Violation, Fine, Status
- Export options (CSV, JSON, Excel)

**Report Generation:**
- Export as CSV: Structured data for analysis
- Export as HTML: Formatted report for sharing/printing

---

## 📈 Accuracy Evaluation

### Manual Evaluation Workflow

**Step 1: Prepare Ground Truth**

Create or edit `evaluation/ground_truth.csv`:
```csv
video_name,frame_number,class_name,confidence
video_1,100,no_helmet,0.95
video_1,110,helmet,0.87
video_2,50,no_helmet,0.92
```

**Step 2: Run Evaluation**

```bash
# Compare predictions with ground truth
python evaluate_accuracy.py

# Output:
# - Precision, Recall, F1-Score
# - Confusion Matrix
# - Per-class metrics
# - Results saved to evaluation/evaluation_results.csv
```

**Step 3: View Results**

```bash
# Quick accuracy summary
python quick_accuracy.py

# Validation dataset accuracy
python val_accuracy.py
```

**Evaluation Metrics Calculated:**
- **Precision**: TP / (TP + FP)
- **Recall**: TP / (TP + FN)
- **F1-Score**: 2 * (Precision * Recall) / (Precision + Recall)
- **Accuracy**: (TP + TN) / Total
- **Confusion Matrix**: True/False Positives/Negatives

---

## 🔧 Troubleshooting

### Database Connection Error
```
Error: could not connect to server: Connection refused
```
**Solution:**
- Verify PostgreSQL is running: `pg_isready`
- Check connection string in `.env`
- Verify database and user exist
- Check firewall settings

### Model Not Found
```
Error: AdvHelmet.pt not found
```
**Solution:**
- Download model from Ultralytics Hub
- Verify MODEL_PATH in `.env` is correct
- Place model in project root: `AdvHelmet.pt`

### Video Processing Hangs
**Solution:**
- Check video format (must be MP4, AVI, MOV, or MKV)
- Verify video is not corrupted: `ffprobe video.mp4`
- Reduce CONFIDENCE threshold to speed up processing
- Check disk space for output results

### CUDA/GPU Not Detected
**Solution:**
```bash
# Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### API Port Already in Use
**Solution:**
```bash
# Change port
python -m uvicorn api:app --port 8001
```

### Streamlit "No module named" Error
**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

---

## 📝 Development Notes

### Key Python Files

**main.py**
- Core video processing pipeline
- Helmet detection logic
- E-challan generation
- CSV/video output

**api.py**
- FastAPI server setup
- File upload handling
- Background job management
- RESTful endpoints

**dashboard.py**
- Streamlit UI components
- Database queries
- Visualization logic
- Report generation

**db.py**
- PostgreSQL connection management
- CRUD operations for challans and detections
- Data validation

**services.py**
- Challan number generation
- SMS notification logic (Twilio)
- License plate extraction (EasyOCR)
- Vehicle detection utilities

**privacy.py**
- Face detection and blurring
- Privacy protection functions

### Data Flow

```
Input Video
    ↓
YOLOv8 Detection (AdvHelmet.pt)
    ↓
ByteTrack Tracking
    ↓
Violation Logic Check
    ↓
E-Challan Generation
    ↓
PostgreSQL Storage
    ↓
CSV Export + Annotated Video Output
    ↓
Dashboard Visualization
```

---

## ⚠️ Important Disclaimers

1. **Educational Purpose**: This system is designed for educational demonstration and research purposes only.

2. **Simulated E-Challan**: All e-challans and fines are simulated. No real penalties are applied or collected.

3. **Privacy Considerations**: 
   - Face blurring is applied for privacy protection
   - Comply with local privacy laws when processing videos
   - Obtain proper consent before recording in public spaces

4. **Optional Features**:
   - SMS notifications require Twilio account credentials
   - License plate reading requires EasyOCR model download
   - These are optional and can be disabled

5. **Model Accuracy**:
   - Model accuracy depends on training data quality
   - Run evaluation to measure performance on your data
   - Manual verification recommended for critical applications

---

## 📚 Dependencies Reference

### Core Dependencies
- **ultralytics**: YOLOv8 object detection
- **opencv-python**: Video processing and annotation
- **pandas**: Data manipulation and CSV operations
- **numpy**: Numerical computations
- **psycopg2-binary**: PostgreSQL database driver

### API & Web
- **fastapi**: RESTful API framework
- **streamlit**: Interactive web dashboard

### Analytics & Visualization
- **plotly**: Interactive charts and graphs
- **scikit-learn**: Machine learning utilities (metrics)

### Optional
- **twilio**: SMS notifications
- **easyocr**: Optical character recognition (license plates)
- **Pillow**: Image processing

See [requirements.txt](requirements.txt) for complete list with versions.

---

## 🎓 Learning Resources

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [PostgreSQL Tutorial](https://www.postgresql.org/docs/)
- [ByteTrack Paper](https://arxiv.org/abs/2110.06864)

---

## 📞 Support & Contribution

For issues, questions, or contributions:
1. Check Troubleshooting section
2. Review error logs in `results/audit.log`
3. Check database connection with `python test_db.py`
4. Review API logs at `http://localhost:8000/docs`

---

## 📄 License

This project is provided as-is for educational purposes.

---

**Last Updated**: January 2025
**Version**: 1.0.0
