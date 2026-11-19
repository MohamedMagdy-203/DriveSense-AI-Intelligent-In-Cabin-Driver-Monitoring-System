# Notebooks

## Purpose

This directory contains executable notebooks and Kaggle execution exports.
Data notebooks preserve raw data and do not perform destructive operations.

## Files

| File | Purpose |
|---|---|
| `phone_detection_data_preparation.ipynb` | Inspects raw YOLO labels and creates the phone-only processed dataset. |
| `phone_detection_training.ipynb` | Fine-tunes and evaluates YOLO11n locally or on Kaggle. |
| `phone_detection_training_kaggle.ipynb` | Executed Kaggle notebook export preserved with outputs. |

For live webcam inference with the trained checkpoint, see
[`experiments/phone_detection/`](../experiments/phone_detection/).

## Phone training workflow

1. Run the preparation notebook only if the raw dataset must be rebuilt.
2. Run `phone_detection_training.ipynb` with GPU enabled.
3. Use the validation split for model selection.
4. Evaluate the test split once after model selection.
5. Download and retain `artifacts/phone_detection/`.

The processed dataset is read-only from the training notebook. Training
artifacts do not belong inside `data/processed/`.
