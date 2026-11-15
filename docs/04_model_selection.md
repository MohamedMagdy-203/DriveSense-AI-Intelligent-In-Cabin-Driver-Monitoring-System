# Face Landmarker Baseline : Model Selection

## 1. Model

- **Available model:** MediaPipe Face Landmarker
- **Pre-trained weights:** `face_landmarker.task` (~3.7 MB, float16) — a single bundle containing three sub-models:
  - **FaceDetector** (BlazeFace short-range, input 192×192)
  - **FaceLandmarker-V2** (input 256×256)
  - **Blendshape** (input 1×146×2)

  Download:
  `https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task`

## 2. Input / Output

- **Input:** Still image, decoded video frame, or live video feed (RGB, arbitrary resolution; internally cropped to 256×256 per detected face)
- **Output:**

| Field | Type | Description |
|---|---|---|
| `faceLandmarks` | `NormalizedLandmark[][]` (x, y ∈ [0, 1]) | 478 3D landmarks per face (468 face mesh + 10 iris), z scaled relative to head center |
| `faceBlendshapes` | `Classifications[]` (score ∈ [0, 1]) | 52 ARKit-style expression coefficients (e.g. `jawOpen`, `eyeBlinkLeft`, `browDownRight`) |
| `facialTransformationMatrixes` | `4×4 float matrix` | Canonical-to-observed face pose transform (optional) |

## 3. Limitations

- **What the model does not do:**
  - No face identity/recognition — only geometry and expression
  - No segmentation or depth map output (landmarks only)
  - No official React Native / Flutter SDK (community wrappers only)
  - No pre-built AR effects or visual effect creator tools
  - No enterprise SLA or commercial support from Google

- **Conditions that may affect performance:**
  - Occlusion (glasses, masks, hands)
  - Extreme pose (near-profile > ~90°)
  - Low lighting / high compression artifacts
  - Very small faces in frame (below effective detection threshold)
  - Mirrored input inverts left/right blendshape labels
  - Multi-face scenes: smoothing only applies when `num_faces = 1`

## 4. Deployment

- **Framework:** TensorFlow Lite (via MediaPipe Tasks API)
- **Runtime:**

| Platform | Runtime |
|---|---|
| Web | WebAssembly (Wasm) + WebGPU/WebGL or XNNPACK CPU |
| Android | minSdk 24 (arm64-v8a, x86_64), Kotlin/Java |
| iOS | 13.0+, Swift/Objective-C |
| Python | `mediapipe` pip package (CPU/GPU delegate) |
| C++ | Native MediaPipe Tasks library |

- **Hardware requirements:** Runs on CPU alone; GPU acceleration (WebGPU, OpenCL, CoreML, XNNPACK) improves throughput. No minimum GPU VRAM requirement documented — model is ~3.7 MB. Tested on Raspberry Pi (CPU-only).
- **License:** **Apache 2.0** — free for commercial use, modification, and redistribution with attribution. No usage limits or API calls required.

## 5. Webcam benchmark

The live-stream benchmark is implemented in
[`experiments/face_landmarker/face_landmarker_benchmark.py`](../experiments/face_landmarker/face_landmarker_benchmark.py).
It runs three 60-second trials for each selected delegate and writes the
measurements to [`experiments/face_landmarker/results.md`](../experiments/face_landmarker/results.md).

From the repository root:

```powershell
python -m pip install -r requirements.txt
Invoke-WebRequest `
  -Uri "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task" `
  -OutFile "models\face_landmarker.task"
python experiments\face_landmarker\face_landmarker_benchmark.py `
  --delegate both --duration 60 --trials 3
```

The report keeps model latency separate from pipeline latency. Model latency is
the time from `detect_async` submission to the asynchronous result callback.
Pipeline latency includes camera capture, RGB conversion, submission, and
optional preview display. Detection failures count callback frames with zero
detected faces; frames whose callback has not arrived after the drain period
are reported separately through the callback-frame count.
