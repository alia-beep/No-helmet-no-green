import os
import re
import uuid
from pathlib import Path

from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

# =========================================================
# LOAD .ENV
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# =========================================================
# CHALLAN NUMBER
# =========================================================

def make_challan_no():
    return "CH-" + uuid.uuid4().hex[:10].upper()


# =========================================================
# NUMBER PLATE OCR
# =========================================================

def read_plate_from_frame(frame):

    try:

        import easyocr

        reader = easyocr.Reader(
            ["en"],
            gpu=False,
            verbose=False
        )

        candidates = []

        for _, text, conf in reader.readtext(frame):

            cleaned = re.sub(
                r"[^A-Z0-9-]",
                "",
                str(text).upper()
            )

            if conf >= 0.35 and len(cleaned) >= 4:

                candidates.append(
                    (conf, cleaned)
                )

        return (
            max(candidates)[1]
            if candidates
            else None
        )

    except Exception as e:

        print("OCR ERROR:", e)

        return None


# =========================================================
# EMAIL
# =========================================================




def send_email(message, subject="Traffic Violation Alert"):

    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")

    print("DEBUG SENDER:", sender)
    print("DEBUG PASSWORD:", "SET" if password else "MISSING")
    print("DEBUG RECEIVER:", receiver)

    if not sender or not password or not receiver:
        print("EMAIL CONFIGURATION MISSING")
        return None, "NOT_CONFIGURED"

    try:

        msg = EmailMessage()

        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = receiver

        msg.set_content(message)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:

            server.login(sender, password)

            server.send_message(msg)

        print("EMAIL SENT SUCCESSFULLY")

        return True, "SENT"

    except Exception as e:

        print("EMAIL ERROR:", e)

        return None, "FAILED"