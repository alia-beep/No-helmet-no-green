import cv2

_CASCADE = None

def _cascade():
    global _CASCADE
    if _CASCADE is None:
        _CASCADE = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
    return _CASCADE

def blur_faces(frame, scale=1.10, neighbors=5):
    if frame is None:
        return frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = _cascade().detectMultiScale(
        gray, scaleFactor=scale, minNeighbors=neighbors, minSize=(30, 30)
    )
    out = frame.copy()
    for x, y, w, h in faces:
        roi = out[y:y+h, x:x+w]
        if roi.size:
            k = max(15, (min(w, h) // 2) * 2 + 1)
            if k % 2 == 0:
                k += 1
            out[y:y+h, x:x+w] = cv2.GaussianBlur(roi, (k, k), 0)
    return out
