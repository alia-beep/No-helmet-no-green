import os
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
load_dotenv()
def get_connection():
    url=os.getenv("DATABASE_URL")
    if not url: raise RuntimeError("DATABASE_URL is missing in .env")
    return psycopg2.connect(url)
@contextmanager
def connection():
    conn=get_connection()
    try: yield conn; conn.commit()
    except Exception: conn.rollback(); raise
    finally: conn.close()
def insert_challan(d):
    sql="""INSERT INTO challans (challan_no,video_name,frame_number,timestamp_seconds,vehicle_number,violation,fine_amount,signal_status,confidence,message_status,payment_status,notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id"""
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql,(d["challan_no"],d.get("video_name"),d.get("frame_number"),d.get("timestamp_seconds"),d.get("vehicle_number"),d.get("violation","NO_HELMET"),d.get("fine_amount",500),d.get("signal_status","RED"),d.get("confidence"),d.get("message_status","NOT_CONFIGURED"),d.get("payment_status","SIMULATED"),d.get("notes")))
            return cur.fetchone()[0]
def insert_detection(d):
    sql="""INSERT INTO detection_events (video_name,frame_number,timestamp_seconds,class_name,confidence,track_id) VALUES (%s,%s,%s,%s,%s,%s)"""
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql,(d.get("video_name"),d.get("frame_number"),d.get("timestamp_seconds"),d.get("class_name"),d.get("confidence"),d.get("track_id")))
def fetch_all(sql,params=None):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur: cur.execute(sql,params or ()); return cur.fetchall()
def fetch_one(sql,params=None):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur: cur.execute(sql,params or ()); return cur.fetchone()
