# 🏗️ System Architecture & Data Flow

## No Helmet No Green Light - Technical Architecture

Visual guide to system components, data flow, and integration points.

---

## 📊 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     INPUT SOURCES                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   📹 Video Files (MP4, AVI, MOV, MKV)                          │
│      ↓                                                           │
│   📤 REST API (FastAPI)                                         │
│      ↓                                                           │
│   🖥️  CLI (Command Line)                                        │
│                                                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                  VIDEO PROCESSING PIPELINE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. 📥 Load Video Frame                                         │
│     ↓                                                            │
│  2. 🤖 YOLOv8 Detection (AdvHelmet.pt)                         │
│     └─ Detect: Person, Helmet, No Helmet                      │
│     ↓                                                            │
│  3. 🔗 ByteTrack Tracking                                       │
│     └─ Track individual persons across frames                  │
│     ↓                                                            │
│  4. ✅ Violation Logic                                          │
│     └─ Check: No helmet = violation?                           │
│     ↓                                                            │
│  5. 🚨 E-Challan Generation                                    │
│     └─ Create violation record                                 │
│     ↓                                                            │
│  6. 🔲 Face Blurring (Privacy)                                 │
│     └─ Blur detected faces                                     │
│     ↓                                                            │
│  7. 💾 Storage & Export                                         │
│     └─ Save results (CSV, Video, DB)                           │
│                                                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATA STORAGE LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🐘 PostgreSQL Database                                         │
│     ├─ Table: detection_events (frame-level)                   │
│     └─ Table: challans (violation records)                     │
│                                                                   │
│  📄 CSV Files                                                    │
│     ├─ video_name_detections.csv                               │
│     └─ audit.log                                               │
│                                                                   │
│  🎬 Processed Videos                                            │
│     └─ video_name_detected.mp4 (with annotations)             │
│                                                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT/PRESENTATION LAYER                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📊 Streamlit Dashboard                                         │
│     ├─ Summary metrics (total, fines, compliance)             │
│     ├─ Interactive charts (Plotly)                             │
│     ├─ Data table (sortable/filterable)                        │
│     └─ Export options (CSV, HTML)                              │
│                                                                   │
│  🔌 REST API (FastAPI)                                         │
│     ├─ /health - Status check                                  │
│     ├─ /jobs - Upload and manage                               │
│     ├─ /jobs/{id} - Check status                               │
│     └─ /docs - Swagger UI                                      │
│                                                                   │
│  📈 Analytics & Reports                                         │
│     ├─ Accuracy metrics (precision, recall)                    │
│     ├─ Violation trends                                        │
│     └─ Compliance reports                                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

### Single Video Processing

```
Input: video.mp4
  │
  ├─→ OpenCV (cv2) reads frame
  │
  ├─→ YOLOv8 Detection Model
  │   └─ Input: Image frame (1080p, RGB)
  │   └─ Output: Bounding boxes with classes and confidence
  │       Example: [{"class": "no_helmet", "conf": 0.95, "bbox": [...]}]
  │
  ├─→ ByteTrack Tracker
  │   └─ Input: Detections from current frame
  │   └─ Output: Same detections with track_id
  │       Example: [{"class": "no_helmet", "conf": 0.95, "track_id": 42}]
  │
  ├─→ Violation Logic
  │   └─ Input: Detection with track_id
  │   ├─ Check: is_no_helmet(class)?
  │   ├─ Check: violation_cooldown passed?
  │   └─ Output: Violation event (if true)
  │
  ├─→ Optional: License Plate Detection (EasyOCR)
  │   └─ Input: Cropped person region
  │   └─ Output: Vehicle number string
  │
  ├─→ Optional: SMS Notification (Twilio)
  │   └─ Input: Challan data
  │   └─ Send: SMS alert (if configured)
  │
  ├─→ Privacy Processing
  │   └─ Input: Frame with detections
  │   └─ Action: Blur detected faces
  │   └─ Output: Blurred frame
  │
  ├─→ Storage
  │   ├─ PostgreSQL: Insert challan record
  │   ├─ CSV: Write detection row
  │   └─ Video: Write annotated frame
  │
  └─→ Output: Detection CSV + Annotated Video
      Files: results/video_detections.csv, results/video_detected.mp4
```

---

## 🏢 Component Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐    │
│  │  main.py     │  │  api.py      │  │  dashboard.py  │    │
│  │              │  │              │  │                │    │
│  │ • Load model │  │ • FastAPI    │  │ • Streamlit UI │    │
│  │ • Process    │  │ • Upload mgmt│  │ • Charts       │    │
│  │   videos     │  │ • Job queue  │  │ • Analytics    │    │
│  └──────┬───────┘  └──────┬───────┘  └────────┬───────┘    │
│         │                 │                    │             │
└─────────┼─────────────────┼────────────────────┼─────────────┘
          │                 │                    │
          └─────────────────┼────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                             │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  services.py                                         │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  • make_challan_no() - Generate unique ID            │   │
│  │  • send_sms() - Twilio notifications                │   │
│  │  • read_plate_from_frame() - EasyOCR                 │   │
│  │  • vehicle_detection() - Identify vehicle            │   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                             │
│  ┌──────────────┼───────────────────────────────────────┐   │
│  │  privacy.py  │                                       │   │
│  ├──────────────┼───────────────────────────────────────┤   │
│  │  • blur_faces() - Face anonymization                 │   │
│  │  • privacy_check() - Compliance                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                 │                                             │
└─────────────────┼─────────────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────────────────────┐
│                    MODEL LAYER                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐    │
│  │  db.py       │  │ ultralytics  │  │  OpenCV (cv2)  │    │
│  │              │  │              │  │                │    │
│  │ • DB connect │  │ • YOLOv8     │  │ • Frame read   │    │
│  │ • CRUD ops   │  │ • Detection  │  │ • Annotation   │    │
│  │ • Queries    │  │ • Tracking   │  │ • Video write  │    │
│  └──────┬───────┘  └──────┬───────┘  └────────┬───────┘    │
│         │                 │                    │             │
└─────────┼─────────────────┼────────────────────┼─────────────┘
          │                 │                    │
          └─────────────────┼────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────┐  ┌──────────────────────────┐   │
│  │  PostgreSQL Database    │  │  File System             │   │
│  ├─────────────────────────┤  ├──────────────────────────┤   │
│  │  • detection_events     │  │  • CSV files             │   │
│  │  • challans             │  │  • MP4 videos            │   │
│  │  • Indexes              │  │  • Log files             │   │
│  └─────────────────────────┘  └──────────────────────────┘   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔌 External Integrations

```
┌────────────────────────────────────────────────────┐
│  OPTIONAL EXTERNAL SERVICES                        │
├────────────────────────────────────────────────────┤
│                                                     │
│  📱 Twilio (SMS)                                  │
│     Used by: services.send_sms()                  │
│     Purpose: Send violation alerts via SMS        │
│     Config: TWILIO_ACCOUNT_SID, AUTH_TOKEN        │
│                                                     │
│  🔤 EasyOCR                                       │
│     Used by: services.read_plate_from_frame()    │
│     Purpose: Extract license plate numbers       │
│     Config: None (auto-downloads model)           │
│                                                     │
│  🔐 OpenAI API (optional)                         │
│     Used by: services (if configured)             │
│     Purpose: Additional analysis                  │
│     Config: OPENAI_API_KEY                        │
│                                                     │
└────────────────────────────────────────────────────┘
```

---

## 📦 Database Schema

```
traffic_ai (PostgreSQL)
│
├── detection_events
│   ├── id (BIGSERIAL PRIMARY KEY)
│   ├── video_name (TEXT)
│   ├── frame_number (INTEGER)
│   ├── timestamp_seconds (DOUBLE)
│   ├── class_name (TEXT) - "helmet" or "no_helmet"
│   ├── confidence (DOUBLE) - 0.0 to 1.0
│   ├── track_id (INTEGER) - Person identity across frames
│   └── created_at (TIMESTAMPTZ)
│
└── challans
    ├── id (BIGSERIAL PRIMARY KEY)
    ├── challan_no (TEXT UNIQUE) - Generated ID
    ├── created_at (TIMESTAMPTZ)
    ├── video_name (TEXT) - Source video
    ├── frame_number (INTEGER)
    ├── timestamp_seconds (DOUBLE)
    ├── vehicle_number (TEXT) - Optional, from OCR
    ├── violation (TEXT) - "NO_HELMET"
    ├── fine_amount (NUMERIC) - Simulated fine
    ├── signal_status (TEXT) - "RED" or "GREEN"
    ├── confidence (DOUBLE)
    ├── message_status (TEXT) - "SENT" or "PENDING"
    ├── payment_status (TEXT) - "PENDING" or "PAID"
    └── notes (TEXT)
```

---

## 🔄 API Request Flow

```
Client (Browser/cURL/Python)
  │
  ├─→ POST /jobs (upload video)
  │   ├─ Validate file format
  │   ├─ Generate job_id (UUID)
  │   ├─ Save file to api_data/uploads/
  │   ├─ Add to job queue
  │   └─ Return: {"job_id": "...", "status": "queued"}
  │
  ├─→ Background Task (run_job)
  │   ├─ Load YOLOv8 model
  │   ├─ Process video frame-by-frame
  │   ├─ Update job status → "processing"
  │   ├─ Save results to database & files
  │   └─ Update job status → "completed" or "failed"
  │
  └─→ GET /jobs/{job_id}
      ├─ Query job from JOBS dictionary
      └─ Return: {"job_id": "...", "status": "completed", ...}
      
      GET /jobs/{job_id}/result
      ├─ Query results CSV file
      └─ Return: CSV content with detections
```

---

## 🎨 Processing Pipeline Detail

```
FRAME PROCESSING LOOP (for each frame):

1. CAPTURE
   └─ cv2.VideoCapture.read() → frame (numpy array)
   
2. DETECTION (YOLOv8)
   ├─ Input: Frame (BGR, e.g., 1920x1080)
   ├─ Model: AdvHelmet.pt
   ├─ Process: 
   │  ├─ Resize to model input size (640x640)
   │  ├─ Normalize pixel values
   │  ├─ Forward pass through YOLOv8
   │  ├─ NMS (Non-Max Suppression)
   │  └─ Filter by confidence threshold
   └─ Output: Detections [{"class": ..., "conf": ..., "bbox": ...}]
   
3. TRACKING (ByteTrack)
   ├─ Input: Current frame detections + previous tracks
   ├─ Algorithm:
   │  ├─ Calculate similarity between detections and tracks
   │  ├─ Match high-confidence detections to tracks
   │  ├─ Start new tracks for unmatched detections
   │  └─ Remove lost tracks
   └─ Output: Detections with track_id
   
4. VIOLATION LOGIC
   ├─ For each detection:
   │  ├─ Is class == "no_helmet"?
   │  ├─ Has violation_cooldown passed for this track_id?
   │  ├─ Is frame_rate normal (not skipped)?
   │  └─ IF all true → VIOLATION DETECTED
   │
   └─ Actions on violation:
      ├─ Generate unique challan_no
      ├─ Create database record
      ├─ Optional: Extract vehicle number (OCR)
      ├─ Optional: Send SMS (Twilio)
      └─ Update violation_cooldown for this track_id
   
5. PRIVACY (Face Blurring)
   ├─ Detect faces using cascade classifier
   ├─ Create blur kernel
   └─ Apply Gaussian blur to face regions
   
6. ANNOTATION
   ├─ Draw bounding boxes
   ├─ Add class labels
   ├─ Add confidence scores
   └─ Add track IDs
   
7. OUTPUT
   ├─ Write frame to output video file
   ├─ Write detection to CSV
   ├─ Write to database
   └─ Write to audit log
```

---

## 🎯 Class Definitions

```
DETECTED CLASSES (by YOLOv8 model):
├─ "helmet" - Person wearing helmet ✓
├─ "no_helmet" - Person without helmet ✗
└─ "person" - Generic person (fallback)

VIOLATION TYPES:
├─ "NO_HELMET" - Primary violation
├─ "RED_LIGHT" - Optional (if signal status tracked)
└─ "SPEEDING" - Optional (if speed detection added)

SIGNAL STATUS:
├─ "RED" - Red light (primary danger time)
├─ "GREEN" - Green light (less risky but still violation)
└─ "UNKNOWN" - If not tracked
```

---

## 📊 Performance Characteristics

```
PROCESSING SPEED:
├─ CPU-based (typical laptop):
│  ├─ Small video (1 min, 1080p): 3-5 minutes
│  ├─ Medium video (5 min, 1080p): 15-25 minutes
│  └─ Large video (10 min, 1080p): 30-50 minutes
│
├─ GPU-based (NVIDIA RTX 3060+):
│  ├─ Small video (1 min, 1080p): 1-2 minutes
│  ├─ Medium video (5 min, 1080p): 5-8 minutes
│  └─ Large video (10 min, 1080p): 10-15 minutes

MEMORY USAGE:
├─ Model loading: ~2GB (GPU) or ~500MB (CPU)
├─ Per-frame processing: ~200-500MB
└─ Database operations: ~100MB per million records

DATABASE SIZE:
├─ Per 1-minute video (30 FPS): ~500KB
├─ Per 1-hour video: ~30MB
└─ Per 1000 violations: ~100KB
```

---

## 🔄 Deployment Architecture

```
SINGLE MACHINE (Development):
┌─────────────────────────────────────┐
│  All in one process                 │
├─────────────────────────────────────┤
│  ├─ API (FastAPI) - Port 8000      │
│  ├─ Dashboard (Streamlit) - 8501   │
│  ├─ Processing (main.py)           │
│  └─ Database client (psycopg2)     │
│                                     │
└───────────┬─────────────────────────┘
            │
            ↓
        PostgreSQL (localhost:5432)

DISTRIBUTED (Production):
┌─────────────────────┐  ┌──────────────┐  ┌─────────────┐
│  API Server         │  │  Processing  │  │  Dashboard  │
│  (FastAPI + Gunicorn│  │  Server      │  │  (Streamlit)│
│  Port 8000)         │  │  (Batch Jobs)│  │  Port 8501  │
└────────────┬────────┘  └──────┬───────┘  └──────┬──────┘
             │                  │                 │
             └──────────────────┼─────────────────┘
                                ↓
                    PostgreSQL Cluster (RDS/Cloud)
                    
Optional:
├─ Redis: Job queue & caching
├─ S3/Cloud Storage: Video storage
├─ Nginx: Reverse proxy & load balancing
└─ Docker: Containerization
```

---

## 🔐 Security Architecture

```
INPUT VALIDATION:
├─ File type check (only video formats)
├─ File size limits
├─ Virus scanning (optional)
└─ Rate limiting (optional)

DATABASE SECURITY:
├─ Connection: SSL/TLS (configurable)
├─ Authentication: User/password (in .env)
├─ Authorization: Per-user database role
├─ Encryption: At-rest (database level)
└─ Backups: Regular automated backups

API SECURITY:
├─ HTTPS (when deployed)
├─ CORS (cross-origin restrictions)
├─ Rate limiting (optional)
├─ API key authentication (optional)
└─ Request validation

PRIVACY:
├─ Face blurring (automatic)
├─ Anonymization: No names stored
├─ Vehicle number: Hashed (optional)
└─ Data retention: Configurable
```

---

## 📈 Monitoring & Logging

```
LOGS LOCATION:
├─ Processing logs: results/audit.log
├─ API logs: stdout (console)
├─ Database logs: PostgreSQL logs
└─ System logs: Operating system logs

LOG LEVELS:
├─ INFO: Normal operations
├─ WARNING: Issues but continued
├─ ERROR: Processing failed
└─ CRITICAL: System failure

METRICS:
├─ Processing time per video
├─ Violations detected per video
├─ Detection accuracy (precision/recall)
├─ Database query time
└─ API response time
```

---

## 🎓 Understanding the Flow

For a **single violation detection**, here's the complete flow:

```
1. Video Frame (1080p image)
   │
   └─→ YOLOv8 sees: Person at coordinates (100,150)
                   with "no_helmet" class
                   confidence 0.95
   
2. ByteTrack identifies
   └─→ This is person #42 (based on appearance)
   
3. Violation check
   ├─ Is "no_helmet"? YES ✓
   ├─ Was person #42 flagged before? NO ✓
   ├─ Is cooldown passed? YES (or first time) ✓
   └─→ VIOLATION DETECTED!
   
4. E-Challan created
   └─→ Challan #GJ2024000001
       Video: traffic.mp4
       Frame: 150
       Time: 5.2 seconds
       Violation: NO_HELMET
       Fine: ₹500
       Track ID: 42
   
5. Optional actions
   ├─ Extract license plate from region → "GJ01AB1234"
   ├─ Send SMS → "+91-XXXXXXXXXX"
   └─ Blur face in video
   
6. Storage
   ├─ Insert into database (challans table)
   ├─ Write to CSV file
   └─ Annotate in video file
   
7. Cooldown set
   └─→ Person #42 won't be flagged again for 10 seconds
```

---

**This architecture is designed to be scalable, modular, and easy to maintain!**
