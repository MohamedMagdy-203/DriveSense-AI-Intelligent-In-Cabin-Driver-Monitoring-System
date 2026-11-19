# Phone Detection Final Artifacts

This directory contains the evaluated YOLO11n phone-detection bundle.

```text
phone_detection/
├── weights/
│   ├── best.pt
│   └── last.pt
├── results/
│   ├── results.csv
│   ├── confusion_matrix.png
│   ├── results.png
│   └── evaluation_metrics.json
├── inference_examples/
└── model_info.txt
```

## Measured results

| Split | Precision | Recall | mAP@50 | mAP@50-95 |
|---|---:|---:|---:|---:|
| Validation | 0.8809 | 0.8649 | 0.9168 | 0.6804 |
| Test | 0.8835 | 0.8202 | 0.8805 | 0.6481 |

The test metrics were evaluated once after validation and model selection.
The test split was not used for tuning.

## Contents

- `weights/best.pt`: selected checkpoint for later inference.
- `weights/last.pt`: final training epoch checkpoint.
- `results/results.csv`: per-epoch losses and detection metrics.
- `results/confusion_matrix.png`: validation confusion matrix.
- `results/results.png`: training and validation curves.
- `results/evaluation_metrics.json`: machine-readable validation/test metrics.
- `inference_examples/`: correct detections, missed detections, false positives,
  and images without phones.
- `model_info.txt`: model and training configuration.

The `.pt` weights are ignored by Git. Keep the files in the local artifact
bundle or download them separately for release distribution.

## Reload

```python
from ultralytics import YOLO

model = YOLO("artifacts/phone_detection/weights/best.pt")
predictions = model.predict(source="image.jpg", imgsz=640, conf=0.25)
```
