# No Helmet No Green Light

AI helmet detection + simulated e-challan + PostgreSQL + Streamlit dashboard.

## Architecture

System Architecture (overview):

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

### Data Flow (single video)

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

## Setup
1. Put your `AdvHelmet.pt` in the project root.
2. Create PostgreSQL database `traffic_ai`.
3. Run `schema.sql` in pgAdmin.
4. Copy `.env.example` to `.env` and set your PostgreSQL password.
5. Install:
   `python -m venv venv`
   `.env\Scripts\Activate.ps1`
   `pip install -r requirements.txt`
6. Test: `python test_db.py`
7. Put up to 10 MP4 videos in `videos/`.
8. Run: `python main.py`
9. Dashboard: `streamlit run dashboard.py`

## Accuracy
Edit `evaluation/ground_truth.csv` with manually verified labels, then run `python evaluate_accuracy.py`.

## Important
The e-challan/fine is simulated for an educational prototype. No real money is deducted. Twilio and OCR are optional.
