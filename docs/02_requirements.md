# System Requirements

## 1. Operational Context

DriveSense AI is a real-time, in-cabin Driver Monitoring System (DMS) designed to monitor driver behavior using computer vision.

The system aims to identify potential signs of:
- Driver drowsiness.
- Visual distraction.
- Mobile phone usage.

### Target Deployment Platforms

- **Initial Development:** PC / Laptop.
- **Camera:** RGB Webcam.
- **Processing:** Local processing.
- **Future Deployment:** Edge AI devices.
- **Deployment Strategy:** Hardware-independent and modular architecture.

## 2. Functional Requirements

| ID | Requirement |
|---|---|
| FR-001 | The system shall capture live video from a compatible RGB camera. |
| FR-002 | The system shall detect and track the driver's face. |
| FR-003 | The system shall monitor eye closure and blinking patterns. |
| FR-004 | The system shall estimate the driver's head orientation. |
| FR-005 | The system shall detect mobile phones within the monitored region. |
| FR-006 | The system shall estimate potential driver interaction with detected mobile phones. |
| FR-007 | The system shall analyze behavioral indicators over time. |
| FR-008 | The system shall combine detection outputs through a Temporal Decision Engine. |
| FR-009 | The system shall generate visual and audio alerts when predefined risk conditions are met. |
| FR-010 | The system shall record relevant detection events and timestamps. |
| FR-011 | The system shall handle unreliable or unavailable visual input appropriately. |

## 3. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-001 | Performance | The system shall support real-time video processing. |
| NFR-002 | Portability | The system shall support PC development and future Edge deployment. |
| NFR-003 | Resource Efficiency | Processing components shall accommodate different hardware capabilities. |
| NFR-004 | Modularity | Detection modules shall be independently replaceable. |
| NFR-005 | Robustness | The system shall be evaluated under varying lighting conditions and head orientations. |
| NFR-006 | Reliability | The system shall account for uncertainty in visual detections. |
| NFR-007 | Maintainability | The codebase shall support future updates and extensions. |
| NFR-008 | Testability | Major system components shall support independent testing. |

## 4. Development Hardware Baseline

| Component | Specification |
|---|---|
| CPU | Intel Core i5-10500H (6 Cores / 12 Threads) |
| RAM | 8 GB DDR4 |
| GPU | NVIDIA GeForce GTX 1650 |
| Dedicated GPU Memory | 4 GB |

## 5. Engineering Constraints

- The system shall not depend on a specific camera model.
- Model inference shall be configurable for CPU or GPU execution.
- Input resolution and processing frequency shall be configurable.
- Video processing shall avoid unnecessary frame buffering.
- Core application logic shall remain independent of the underlying hardware.

## 6. Performance Evaluation Metrics

The system will be evaluated using:

- Video Processing FPS.
- Model Inference FPS.
- End-to-End Latency.
- CPU and GPU Utilization.
- RAM and GPU Memory Consumption.
- Detection Performance.

Specific performance targets will be established after initial benchmarking.

## 7. Scope Limitations

The initial version will not include:

- Vehicle control or autonomous driving.
- Medical diagnosis.
- Driver identity recognition.
- Passenger monitoring.
- Safety certification or guarantees of accident prevention.