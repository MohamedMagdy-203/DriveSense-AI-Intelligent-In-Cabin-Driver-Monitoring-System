# Data

## Directory contract

```text
data/
├── raw/
│   └── reorganized_dataset/
└── processed/
    └── phone_detection/
        ├── images/{train,val,test}/
        ├── labels/{train,val,test}/
        └── data.yaml
```

`raw/` contains the original data and must not be modified. Training and
analysis use copies under `processed/`.

The phone-only processed dataset contains YOLO normalized labels:

```text
0 x_center y_center width height
```

Here `0` means phone and `1` has been excluded. Negative samples have matching
label files that are empty.

Raw and processed datasets are intentionally ignored by Git in this repository.
