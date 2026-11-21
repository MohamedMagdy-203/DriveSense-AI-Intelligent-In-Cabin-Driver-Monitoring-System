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

Fresh clones do not contain the ignored `.pt` weights. The local runtime
requires `weights/best.pt` at the path above. Reproduce the artifact by running
the training notebook or copy the verified local checkpoint bundle into the
same directory. This repository does not provide an unverified external weight
download link.

After copying a verified checkpoint bundle, prepare and verify it with:

```powershell
python scripts/prepare_phone_artifacts.py C:\path\to\phone_detection_bundle
python scripts/prepare_phone_artifacts.py --verify-only
```

The tracked
[`model_manifest.json`](model_manifest.json)
records the verified SHA-256 values for this project's local artifact bundle.
The manifest is integrity metadata, not a proof of dataset or runtime
generalization.

## Reload

```python
from ultralytics import YOLO

model = YOLO("artifacts/phone_detection/weights/best.pt")
predictions = model.predict(source="image.jpg", imgsz=640, conf=0.25)
```
