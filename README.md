# Medical Physics Quality Control Auditor

## Overview
This project is an automated Quality Control (QC) auditing system designed for medical imaging and radiation therapy equipment. It simulates and analyzes daily performance logs for critical medical devices, including Linear Accelerators (Linacs), CT Scanners, MRI machines, and Gamma Cameras.

The system automates compliance checking against standard protocols (AAPM TG-142, TG-66, ACR, and NEMA) and implements predictive maintenance logic to detect equipment degradation before failure occurs.

## Features
- **Automated Compliance Auditing:** Checks daily machine metrics against configurable absolute tolerances.
- **Predictive Maintenance Detection:** Uses linear regression to detect statistically significant drift in machine performance over time.
- **Multi-Modality Support:** Handles distinct logic for Linacs, CT, MRI, and Nuclear Medicine equipment.
- **Data Persistence:** Archives all audit records to a SQLite database (`qc_history.db`) for long-term trend analysis.
- **Visual Reporting:** Automatically generates control charts for every machine-metric pair to visualize trends and pass/fail limits.
- **Dockerised Environment:** Fully containerized application for consistent execution across different platforms.

## Supported Protocols
The system is configured to audit against specific medical physics standards:
1.  **Linac (Radiation Therapy):** AAPM Task Group 142 (Daily Output & Symmetry).
2.  **CT Simulator:** AAPM Task Group 66 (Water density calibration/HU).
3.  **MRI Scanner:** ACR MRI QC Manual (SNR & Geometric Distortion).
4.  **Gamma Camera:** NEMA NU-1 (Integral Uniformity).

## Project Structure
```text
.
├── config.yaml
├── demo_results
│   ├── daily_qc_log.xlsx
│   ├── qc_audit.log
│   ├── qc_history.db
│   └── qc_reports
│       ├── audit_results.xlsx
│       └── plots
│           ├── CT_Scanner_A_Water_HU.png
│           ├── Gamma_Cam_SPECT_Uniformity.png
│           ├── Linac_1_Dose_Output.png
│           ├── Linac_1_Symmetry.png
│           ├── MRI_Scanner_3T_Geometric_Distortion.png
│           └── MRI_Scanner_3T_SNR_Coil_1.png
├── Dockerfile
├── generate_data.py
├── main.py
└── README.md
```
## Configuration (config.yaml)

The auditing logic is driven by the config.yaml file. This file allows users to define the "passing rules" without modifying the code. It maps specific machines to their required metrics, target values, and absolute tolerances.

Example structure:

```YAML
Linac_1:
  Dose_Output:
    target: 100.0
    tolerance_abs: 2.0  # Fails if value > 102.0 or < 98.0
    unit: "cGy"
```
*Modify this file to adjust strictness or add new machines to the audit scope.*

## Setup and Usage

### Prerequisites

-  **Docker**

### Running via Docker

1.   **Build the image**

```bash
docker build -t qc-auditor .
```

2.   **Generate Data**

```bash
docker run --rm --entrypoint python -v $(pwd):/app qc-auditor generate_data.py
```

3.   **Run analysis**

```bash
docker run --rm -v $(pwd):/app qc-auditor --input daily_qc_log.xlsx
```
   
## Outputs

After execution, the ***qc_reports/*** directory will contain:

-   **audit_results.xlsx**: A comprehensive log of every measurement with its Pass/Fail status.
-   **plots/**: Time-series control charts showing the measured values relative to the Upper and Lower Control Limits.

### Examples of plots (All available in *demo_results/* ):

<img width="865" height="456" alt="Screenshot 2026-01-11 at 22 00 34" src="https://github.com/user-attachments/assets/4a44b214-7bb9-4b24-9bbd-e3309cade347" />

<img width="865" height="459" alt="Screenshot 2026-01-11 at 22 01 07" src="https://github.com/user-attachments/assets/7615c7c9-ee07-4e76-a274-14d1a53764fd" />

<img width="864" height="456" alt="Screenshot 2026-01-11 at 22 01 45" src="https://github.com/user-attachments/assets/ff91a712-0c19-4298-9fd4-0ea7e51b916b" />





