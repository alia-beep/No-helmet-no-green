import os, csv, logging
from pathlib import Path
from collections import defaultdict
import cv2
from ultralytics import YOLO
from dotenv import load_dotenv
from db import insert_challan, insert_detection
from services import make_challan_no, send_sms, read_plate_from_frame
from privacy import blur_faces

load_dotenv()
MODEL_PATH=os.getenv("MODEL_PATH","AdvHelmet.pt")
VIDEO_DIR=Path(os.getenv("VIDEO_DIR","videos")); OUTPUT_DIR=Path(os.getenv("OUTPUT_DIR","results"))
CONFIDENCE=float(os.getenv("CONFIDENCE","0.25")); FINE_AMOUNT=float(os.getenv("FINE_AMOUNT","500"))
COOLDOWN=float(os.getenv("VIOLATION_COOLDOWN_SECONDS","10"))
VIDEO_DIR.mkdir(exist_ok=True); OUTPUT_DIR.mkdir(exist_ok=True)
logging.basicConfig(filename=OUTPUT_DIR/"audit.log",level=logging.INFO,format="%(asctime)s | %(levelname)s | %(message)s")

def norm(s): return str(s).lower().replace("_"," ").replace("-"," ").strip()
def no_helmet(s):
    n=norm(s); return "no helmet" in n or "nohelmet" in n or "without helmet" in n
def helmet(s):
    n=norm(s); return "helmet" in n and not no_helmet(n)

def process_video(path,model,show_window=True):
    cap=cv2.VideoCapture(str(path))
    if not cap.isOpened(): print(f"Cannot open {path}"); return
    fps=cap.get(cv2.CAP_PROP_FPS) or 25
    w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_path=OUTPUT_DIR/f"{path.stem}_detected.mp4"; csv_path=OUTPUT_DIR/f"{path.stem}_detections.csv"
    out=cv2.VideoWriter(str(out_path),cv2.VideoWriter_fourcc(*"mp4v"),fps,(w,h))
    cf=open(csv_path,"w",newline="",encoding="utf-8"); cw=csv.writer(cf)
    cw.writerow(["frame","timestamp","class","confidence","track_id","x1","y1","x2","y2"])
    frame_no=0; last=defaultdict(lambda:-999999); challans=0
    while True:
        ok,frame=cap.read()
        if not ok: break
        frame_no+=1; ts=frame_no/fps
        try: result=model.track(frame,conf=CONFIDENCE,persist=True,tracker="bytetrack.yaml",verbose=False)[0]
        except Exception: result=model.predict(frame,conf=CONFIDENCE,verbose=False)[0]
        helmets=[]; violations=[]
        if result.boxes is not None:
            for b in result.boxes:
                cid=int(b.cls[0].cpu().numpy()); conf=float(b.conf[0].cpu().numpy())
                name=str(model.names[cid]); x1,y1,x2,y2=b.xyxy[0].cpu().numpy().astype(int)
                tid=int(b.id[0].cpu().numpy()) if b.id is not None else None
                cw.writerow([frame_no,round(ts,2),name,round(conf,4),tid,x1,y1,x2,y2])
                try: insert_detection({"video_name":path.name,"frame_number":frame_no,"timestamp_seconds":ts,"class_name":name,"confidence":conf,"track_id":tid})
                except Exception as e: logging.error("Detection DB: %s",e)
                item={"confidence":conf,"track_id":tid}
                if no_helmet(name): violations.append(item)
                elif helmet(name): helmets.append(item)
        signal="RED" if violations else "GREEN"
        if violations:
            best=max(violations,key=lambda x:x["confidence"]); key=best["track_id"] if best["track_id"] is not None else "unknown"
            if ts-last[key]>=COOLDOWN:
                plate=read_plate_from_frame(frame) or "NOT_READ"; challan=make_challan_no()
                msg=f"Traffic Violation\nNo Helmet Detected\nVehicle: {plate}\nFine: Rs.{int(FINE_AMOUNT)}\nChallan: {challan}\nEducational simulation"
                _,sms_status=send_sms(msg)
                try:
                    insert_challan({"challan_no":challan,"video_name":path.name,"frame_number":frame_no,"timestamp_seconds":ts,"vehicle_number":plate,"violation":"NO_HELMET","fine_amount":FINE_AMOUNT,"signal_status":"RED","confidence":best["confidence"],"message_status":sms_status,"payment_status":"SIMULATED","notes":"Educational prototype; no real money deducted."})
                except Exception as e: logging.error("Challan DB: %s",e)
                last[key]=ts; challans+=1
        annotated=result.plot()
        if os.getenv("BLUR_FACES","true").lower() in {"1","true","yes"}:
            annotated=blur_faces(annotated)
        cv2.rectangle(annotated,(0,0),(w,125),(30,30,30),-1)
        color=(0,0,255) if signal=="RED" else (0,200,0)
        cv2.putText(annotated,f"SIGNAL: {signal}",(20,38),cv2.FONT_HERSHEY_SIMPLEX,1,color,3)
        cv2.putText(annotated,f"Helmet: {len(helmets)}   No Helmet: {len(violations)}",(20,75),cv2.FONT_HERSHEY_SIMPLEX,.7,(255,255,255),2)
        text=f"E-CHALLAN: Rs.{int(FINE_AMOUNT)} | SIMULATED" if violations else "NO VIOLATION - GREEN LIGHT"
        cv2.putText(annotated,text,(20,108),cv2.FONT_HERSHEY_SIMPLEX,.65,(0,180,255) if violations else (0,220,0),2)
        out.write(annotated)
        if show_window:
            cv2.imshow("No Helmet - No Green Light",annotated)
            if cv2.waitKey(1)&0xFF==ord("q"): break
    cap.release(); out.release(); cf.close()
    if show_window: cv2.destroyAllWindows()
    return {"video":path.name,"output_video":str(out_path),"detections_csv":str(csv_path),"challans":challans}

def main():
    if not Path(MODEL_PATH).exists(): raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
    videos=sorted(VIDEO_DIR.glob("*.mp4"))[:10]
    if not videos: raise FileNotFoundError("Put MP4 videos inside videos folder.")
    model=YOLO(MODEL_PATH); print("Model classes:",model.names)
    for v in videos: process_video(v,model)
    print("ALL VIDEOS COMPLETED")
if __name__=="__main__": main()
