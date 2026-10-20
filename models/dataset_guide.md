# Leaf Disease Detection Dataset & Custom Training Guide

This guide details how to train or fine-tune YOLOv8 models for specialized leaf diseases on your agricultural land.

---

## 1. Pre-Trained Datasets
For agricultural leaf disease detection, the following open datasets provide excellent bounding-box annotations:
- **PlantVillage Dataset**: 54,000+ images across 14 crop species and 26 diseases (Apple scab, Corn blight, Tomato late blight, Potato early blight, etc.).
- **Roboflow Plant Doc Dataset**: 2,598 images with annotated bounding boxes formatted for YOLOv8.
- **Kaggle Rice & Wheat Leaf Disease Datasets**.

---

## 2. Preparing Dataset in YOLOv8 Format
Organize your dataset folder structure as follows:

```
dataset/
├── data.yaml
├── train/
│   ├── images/
│   └── labels/
└── val/
    ├── images/
    └── labels/
```

### `data.yaml` Example:
```yaml
path: ../dataset
train: train/images
val: val/images

names:
  0: healthy_leaf
  1: early_blight
  2: late_blight
  3: leaf_spot
  4: powdery_mildew
  5: rust
```

---

## 3. Training Command (YOLOv8 Nano for Raspberry Pi / Edge)
To train a model lightweight enough for high FPS on Raspberry Pi 4/5:

```bash
# In your terminal with GPU (or Google Colab / Kaggle):
yolo detect train \
  data=data.yaml \
  model=yolov8n.pt \
  epochs=50 \
  imgsz=640 \
  batch=16 \
  name=agri_leaf_disease
```

Once training finishes, copy `runs/detect/agri_leaf_disease/weights/best.pt` to:
`models/yolov8n_leaf_disease.pt` in this project.

---

## 4. Raspberry Pi Optimization (NCNN / ONNX Export)
To achieve 25-30+ FPS on Raspberry Pi 4/5, export your model to NCNN or ONNX:

```python
from ultralytics import YOLO

# Load your trained model
model = YOLO("models/yolov8n_leaf_disease.pt")

# Export to NCNN (Fastest on Raspberry Pi CPU)
model.export(format="ncnn")
```
Update `rover_config.yaml` to point to the exported model directory or `.onnx` file.
