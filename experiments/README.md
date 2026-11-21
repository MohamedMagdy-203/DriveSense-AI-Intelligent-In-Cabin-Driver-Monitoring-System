# Experiments

The experiments directory preserves the project's calibration, benchmarking,
data-collection, validation, and live-demo history. Scripts here are not the
production API.

Reusable algorithms live under `src/drivesense/`. Experiment scripts import
those modules and add procedures, camera interaction, reporting, or
visualization specific to the experiment.

Main areas:

- `face_landmarker/`: landmark inspection, eye calibration, eye closure,
  geometric gaze calibration, and live demos.
- `head_pose/`: matrix inspection, controlled-motion recording, axis
  validation, and live monitoring.
- `video_processing/`: OpenCV, GStreamer, and MediaPipe benchmarks.
- `../notebooks/`: dataset preparation and phone-object-detection training
  notebooks.
- `../artifacts/phone_detection/`: final trained-model outputs, plots,
  metrics, and representative inference examples.

Hardware-dependent scripts should be run manually with the configured Windows
virtual environment. Their stored CSV and Markdown outputs are research
artifacts and should not be treated as production validation.

For clarity, live-camera results are separately labeled as Live Webcam
Testing. A short integrated webcam probe processed 139 frames over approximately
5 seconds with a `640x480` camera feed. It produced `AVAILABLE` Face,
`ON_REFERENCE` Gaze, `ATTENTIVE` gaze assessment, `OPEN` Drowsiness, `0%`
PERCLOS, and `ATTENTIVE` Distraction. This is a single-condition integration
check, not a broad accuracy or protocol-validation claim.
