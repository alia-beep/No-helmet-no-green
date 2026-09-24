from ultralytics import YOLO

model = YOLO("AdvHelmet.pt")

results = model.val(
    data="data.yaml",
    split="val"
)

print("Precision:", results.box.mp)
print("Recall:", results.box.mr)
print("mAP50:", results.box.map50)
print("mAP50-95:", results.box.map)