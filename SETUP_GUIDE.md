# Installation & Setup Guide

## No Helmet No Green Light - Complete Setup

Step-by-step guide for setting up the traffic enforcement AI system.

---

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Python Environment Setup](#python-environment-setup)
3. [PostgreSQL Database Setup](#postgresql-database-setup)
4. [Project Dependencies](#project-dependencies)
5. [Configuration](#configuration)
6. [Verification & Testing](#verification--testing)
7. [First Run](#first-run)
8. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware
- **CPU**: Intel i5/i7 or equivalent (or ARM for Raspberry Pi)
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: NVIDIA/CUDA compatible (optional but recommended)
- **Storage**: 10GB free space minimum
- **Internet**: For downloading models and dependencies

### Software
- **Python**: 3.8, 3.9, 3.10, or 3.11 (not 3.12 yet due to dependencies)
- **PostgreSQL**: 12.0 or higher
- **Git** (optional, for cloning repository)
- **Visual C++ Build Tools** (Windows only)

### Check Your System
```bash
# Check Python version
python --version

# Check pip
pip --version

# Check OS
python -c "import platform; print(platform.platform())"

# Check available RAM
python -c "import psutil; print(f'RAM: {psutil.virtual_memory().available / (1024**3):.2f} GB')"
```

---

## Python Environment Setup

### Step 1: Install Python

**Windows:**
1. Download from https://www.python.org/downloads/
2. Run installer, check "Add Python to PATH"
3. Choose "Install for all users" or "Current user"

**macOS:**
```bash
brew install python@3.11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### Step 2: Create Project Directory

```bash
# Create directory
mkdir -p d:\traffic_ai
cd d:\traffic_ai

# Or for existing project
cd d:\no_green_no_light
```

### Step 3: Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate (Windows - PowerShell)
venv\Scripts\Activate.ps1

# Activate (Windows - CMD)
venv\Scripts\activate.bat

# Activate (Linux/macOS)
source venv/bin/activate

# Verify activation (should show (venv) in terminal)
which python  # Linux/macOS
where python  # Windows
```

### Step 4: Upgrade pip and setuptools

```bash
python -m pip install --upgrade pip setuptools wheel
```

---

## PostgreSQL Database Setup

### Installation

**Windows:**
1. Download from https://www.postgresql.org/download/windows/
2. Run installer, remember password for postgres user
3. Port: 5432 (default)
4. Install pgAdmin (included)

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu):**
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Create Database and User

**Method 1: Using pgAdmin (GUI)**
1. Open pgAdmin
2. Right-click "Databases" → "Create" → "Database"
3. Name: `traffic_ai`
4. Create user: `traffic_user` with password

**Method 2: Using psql (Command Line)**

```bash
# Connect as default user
psql -U postgres

# Inside psql:
CREATE DATABASE traffic_ai;
CREATE USER traffic_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE traffic_ai TO traffic_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO traffic_user;
\q  # Exit psql
```

### Load Database Schema

```bash
# Make sure you're in project directory
cd d:\no_green_no_light

# Load schema (Windows)
psql -U traffic_user -d traffic_ai -f schema.sql

# Load schema (Linux/macOS)
psql -U traffic_user -d traffic_ai < schema.sql

# Verify tables created
psql -U traffic_user -d traffic_ai -c "\dt"
```

**Expected output:**
```
         List of relations
 Schema | Name | Type  | Owner
--------+------+-------+-----------
 public | challans | table | traffic_user
 public | detection_events | table | traffic_user
```

### Test Connection

```bash
# Test connection
psql -U traffic_user -d traffic_ai -c "SELECT 1 as connection_test;"

# Output should be: connection_test = 1
```

---

## Project Dependencies

### Step 1: Clone or Download Project

```bash
# If using Git
git clone <repository-url> d:\no_green_no_light
cd d:\no_green_no_light

# Or navigate to existing directory
cd d:\no_green_no_light
```

### Step 2: Install Python Requirements

```bash
# Basic installation
pip install -r requirements.txt

# With enhanced features (OCR, SMS, etc.)
pip install -r requirements_enhanced.txt

# Or install individually
pip install ultralytics opencv-python pandas numpy psycopg2-binary python-dotenv streamlit plotly
```

### Step 3: Verify Installation

```bash
# Check installed packages
pip list

# Check specific packages
python -c "import cv2; print('OpenCV:', cv2.__version__)"
python -c "import pandas; print('Pandas:', pandas.__version__)"
python -c "from ultralytics import YOLO; print('YOLOv8 available')"
python -c "import psycopg2; print('PostgreSQL driver available')"
python -c "import streamlit; print('Streamlit available')"
```

---

## Configuration

### Step 1: Create .env File

```bash
# Copy example
cp .env.example .env

# Or create new (Windows PowerShell)
New-Item -Path ".env" -ItemType File

# Or create new (Linux/macOS)
touch .env
```

### Step 2: Edit .env with Your Settings

```env
# ==================== DATABASE ====================
DATABASE_URL=postgresql://traffic_user:your_secure_password@localhost:5432/traffic_ai
DB_HOST=localhost
DB_PORT=5432
DB_USER=traffic_user
DB_PASSWORD=your_secure_password
DB_NAME=traffic_ai

# ==================== MODEL ====================
MODEL_PATH=AdvHelmet.pt
CONFIDENCE=0.25

# ==================== PROCESSING ====================
FINE_AMOUNT=500
VIDEO_DIR=videos
OUTPUT_DIR=results
VIOLATION_COOLDOWN_SECONDS=10

# ==================== API ====================
API_HOST=0.0.0.0
API_PORT=8000
API_UPLOAD_DIR=api_data/uploads

# ==================== OPTIONAL: TWILIO SMS ====================
# TWILIO_ACCOUNT_SID=your_sid_here
# TWILIO_AUTH_TOKEN=your_token_here
# TWILIO_PHONE_NUMBER=+1234567890

# ==================== OPTIONAL: OCR ====================
# OPENAI_API_KEY=your_key_here
```

### Step 3: Create Directories

```bash
# Create required directories
mkdir -p videos
mkdir -p results
mkdir -p api_data/uploads
mkdir -p evaluation
mkdir -p reports

# Verify
ls -la videos results api_data/uploads  # Linux/macOS
dir videos results api_data\uploads      # Windows
```

---

## Get the AI Model

### Option 1: Use Existing Model

If you already have `AdvHelmet.pt`:
```bash
# Place in project root
cp /path/to/AdvHelmet.pt ./AdvHelmet.pt

# Verify file exists
ls -la AdvHelmet.pt  # Linux/macOS
dir AdvHelmet.pt     # Windows
```

### Option 2: Download from Ultralytics

```bash
# Download YOLOv8 nano model (fastest)
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Download YOLOv8 small model (accurate)
python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"

# Rename to AdvHelmet.pt for compatibility
cp ~/.yolo/weights/detect/yolov8n.pt ./AdvHelmet.pt
```

### Step 4: Verify Model

```bash
# Test model loading
python -c "from ultralytics import YOLO; model = YOLO('AdvHelmet.pt'); print('Model loaded successfully')"
```

---

## Verification & Testing

### Step 1: Test Database Connection

```bash
# Run test script
python test_db.py

# Expected output:
# ✓ Connected to PostgreSQL
# ✓ Database: traffic_ai
# ✓ Tables found: 2
# ✓ Test complete
```

### Step 2: Test Environment Setup

```bash
# Python packages
python -c "
import sys
print(f'Python: {sys.version}')
import cv2; print(f'OpenCV: {cv2.__version__}')
import pandas; print(f'Pandas: {pandas.__version__}')
import numpy; print(f'NumPy: {numpy.__version__}')
from ultralytics import YOLO; print('YOLOv8: OK')
import psycopg2; print('psycopg2: OK')
import streamlit; print('Streamlit: OK')
"
```

### Step 3: Test File Structure

```bash
# Check all required files/dirs
python -c "
from pathlib import Path
required = ['AdvHelmet.pt', 'main.py', 'api.py', 'dashboard.py', 
            'db.py', 'schema.sql', '.env', 'videos', 'results']
for item in required:
    exists = Path(item).exists()
    status = '✓' if exists else '✗'
    print(f'{status} {item}')
"
```

---

## First Run

### Option 1: Batch Video Processing

```bash
# 1. Place videos in videos/ directory
cp sample_video.mp4 videos/

# 2. Run processing
python main.py

# 3. Check results
ls results/
```

### Option 2: Start Dashboard

```bash
# 1. Start Streamlit
streamlit run dashboard.py

# 2. Browser opens at http://localhost:8501
# 3. View statistics and results
```

### Option 3: Start API Server

```bash
# 1. Start API
python -m uvicorn api:app --reload --port 8000

# 2. Open http://localhost:8000/docs
# 3. Upload video via UI
```

---

## Troubleshooting

### Python Issues

**"python command not found"**
```bash
# Windows: Add Python to PATH
# Control Panel → System → Environment Variables
# Add Python installation path to PATH

# Linux/macOS:
which python3
alias python=python3
```

**"ModuleNotFoundError"**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Or individual module
pip install ultralytics
```

**"Virtual environment not activated"**
```bash
# Check prompt - should show (venv)
# Reactivate:
source venv/bin/activate  # Linux/macOS
venv\Scripts\Activate.ps1 # Windows PS
```

### PostgreSQL Issues

**"Connection refused"**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Windows: Start service
net start postgresql-x64-14

# Linux: Start service
sudo systemctl start postgresql

# macOS: Start service
brew services start postgresql
```

**"role traffic_user does not exist"**
```bash
# Recreate user
psql -U postgres
CREATE USER traffic_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE traffic_ai TO traffic_user;
\q
```

**"Database traffic_ai does not exist"**
```bash
# Recreate database
psql -U postgres
CREATE DATABASE traffic_ai;
\q

# Then run schema
psql -U traffic_user -d traffic_ai -f schema.sql
```

### Model Issues

**"AdvHelmet.pt not found"**
```bash
# Download model
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Copy to project
cp ~/.yolo/weights/detect/yolov8n.pt ./AdvHelmet.pt
```

**"CUDA not found" (GPU)**
```bash
# Install CUDA PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Or use CPU version
pip install torch torchvision torchaudio
```

### Directory Issues

**"videos directory not found"**
```bash
# Create required directories
mkdir -p videos results api_data/uploads evaluation reports
```

**"Permission denied" writing to results**
```bash
# Fix permissions
chmod 755 results  # Linux/macOS
icacls results /grant %USERNAME%:F  # Windows
```

---

## Environment Verification Checklist

```bash
✓ Python 3.8+ installed
✓ PostgreSQL 12+ installed and running
✓ Virtual environment created and activated
✓ All pip packages installed
✓ Database created: traffic_ai
✓ User created: traffic_user
✓ Schema loaded
✓ .env configured with correct credentials
✓ AdvHelmet.pt model exists
✓ directories created: videos, results, etc.
✓ test_db.py passes
✓ Model loads successfully
```

---

## Next Steps

1. **Add sample videos** to `videos/` directory
2. **Run main.py** to process videos
3. **Check results** in `results/` directory
4. **Start dashboard** with `streamlit run dashboard.py`
5. **Explore API** at `http://localhost:8000/docs`

---

## Support Resources

- **Main Documentation**: README_COMPREHENSIVE.md
- **Quick Start**: QUICKSTART.md
- **API Reference**: API_REFERENCE.md
- **Project Issues**: Check results/audit.log
- **Database Logs**: Check PostgreSQL logs

Happy setup! 🚀
