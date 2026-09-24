from ultralytics import YOLO
import cv2,os,csv
MODEL_PATH="AdvHelmet.pt"; VIDEO_DIR="videos"; OUTPUT_DIR="results"; CONFIDENCE=.25
os.makedirs(OUTPUT_DIR,exist_ok=True); model=YOLO(MODEL_PATH)
videos=sorted([os.path.join(VIDEO_DIR,x) for x in os.listdir(VIDEO_DIR) if x.lower().endswith(".mp4")])[:10]
print("Classes:",model.names)
for video_path in videos:
    cap=cv2.VideoCapture(video_path)
    if not cap.isOpened(): print("Cannot open",video_path); continue
    fps=cap.get(cv2.CAP_PROP_FPS) or 25; w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    name=os.path.splitext(os.path.basename(video_path))[0]; out=cv2.VideoWriter(os.path.join(OUTPUT_DIR,name+"_detected.mp4"),cv2.VideoWriter_fourcc(*"mp4v"),fps,(w,h))
    cf=open(os.path.join(OUTPUT_DIR,name+"_detections.csv"),"w",newline="",encoding="utf-8"); cw=csv.writer(cf); cw.writerow(["frame","class","confidence","x1","y1","x2","y2"])
    frame=0
    while True:
        ok,img=cap.read()
        if not ok: break
        frame+=1; r=model.predict(img,conf=CONFIDENCE,verbose=False)[0]
        if r.boxes is not None:
            for b in r.boxes:
                x1,y1,x2,y2=b.xyxy[0].cpu().numpy(); conf=float(b.conf[0].cpu().numpy()); cid=int(b.cls[0].cpu().numpy())
                cw.writerow([frame,model.names[cid],round(conf,4),int(x1),int(y1),int(x2),int(y2)])
        out.write(r.plot())
    cap.release(); out.release(); cf.close()
print("ALL VIDEOS COMPLETED")
