# fathomnet-voxel51

**Voxel51 Customer Success Onboarding Project**

This repo contains the workflow and analysis for the [FathomNet 2025 dataset](https://www.kaggle.com/competitions/fathomnet-2025/) (CVPR-FGVC) using [FiftyOne Enterprise](https://docs.voxel51.com/enterprise/index.html). The project simulates a real-world Customer Success scenario involving scientific data curation, hierarchical taxonomy analysis, and "needle-in-a-haystack" visual search for marine research (MBARI).

## Repo Structure

```text
.
├── data/
│   ├── dataset_test.json       # FathomNet Test annotations (COCO format)
│   └── dataset_train.json      # FathomNet Train annotations (COCO format)
├── fathomnet-voxel51/
│   ├── __init__.py
│   ├── check_gcp_auth.py       # Script to verify GCP authentication
│   ├── download_data.py        # Script to fetch images and upload to Cloud Storage
│   ├── ingest_dataset.py       # Script to ingest data into FiftyOne
│   └── load_data_gcp.py        # Script to load data from GCP
├── notebooks/
│   ├── 00_load_data_gcp.ipynb  # Example notebook for loading data from GCP
│   └── fathomnet-2025-cvpr-fgvc.ipynb  # Initial EDA and data exploration
├── pyproject.toml              # Project dependencies and configuration
└── README.md
```

## Project Overview

**Customer Profile:** Marine Research Institute (MBARI)

**Challenge:** Managing 79 hierarchical categories of marine life, identifying mislabeled samples, and discovering anomalies (trash, ROV equipment) in vast amounts of visual data.

**Key Workflows Implemented:**

1. **Cloud-Backed Ingestion:** Efficiently ingesting COCO datasets where images reside in Google Cloud Storage (GCS) without local duplication.

2. **Embeddings & Visualization:** Using CLIP/ResNet to visualize the taxonomic distance between species.

3. **Similarity Search:** Text-to-Image search to distinguish between sub-species (e.g., Octopus rubescens vs. Octopus cyanea).

4. **Zero-Shot Prediction:** Leveraging the [`@voxel51/zero-shot-prediction`](https://docs.voxel51.com/plugins/plugins_ecosystem/zero_shot_prediction.html) plugin to bootstrap labels for unknown objects (e.g., "plastic bag").

## Setup & Installation

### 1. Environment

Ensure you have Python 3.9+ installed. It is recommended to use a virtual environment.

```bash
# Create and activate virtual env
uv venv .venv
source .venv/bin/activate
```

### 2. Dependencies

Install dependencies using `uv`:

```bash
uv pip install -e .
```

> _Note: This project requires fiftyone, google-cloud-storage, and standard data science libraries._

### 3. Credentials

You will need the following credentials set in your environment. The project uses `python-dotenv` to load these from a `.env` file in the project root.

1.  Create a file named `.env` in the root directory: `touch .env`
2.  Add the following variables to it:

```env
# FiftyOne Enterprise
FIFTYONE_API_URI="https://<your-deployment>.fiftyone.ai"
FIFTYONE_API_KEY="<your-api-key>"

# GCP (required)
GOOGLE_CLOUD_PROJECT="<your-gcp-project-id>"

# GCP Service Account (optional - only if not using ADC)
# GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/gcp_credentials.json"
```

#### GCP Authentication Options

- **Application Default Credentials (ADC)** _(recommended for local development)_: Run `gcloud auth application-default login`. No `GOOGLE_APPLICATION_CREDENTIALS` needed.
- **Service Account Key**: Set `GOOGLE_APPLICATION_CREDENTIALS` to the path of your service account JSON key file. Useful for CI/CD or production environments.

> **Note:** The `GOOGLE_CLOUD_PROJECT` is always required for the notebook environment to correctly identify your GCP project.

To verify your GCP authentication setup, run:

```bash
python -m fathomnet_voxel51.check_gcp_auth
```

## Usage

### Data Ingestion

The dataset relies on images hosted via URLs. We use a staging approach:

1. Download images from FathomNet URLs.
2. Upload to a private GCS Bucket (gs://voxel51-test/fathomnet/...).
3. Create FiftyOne samples pointing to the Cloud URI.

Run the ingestion script:

```bash
python -m fathomnet_voxel51.download_data
```

### Exploration

To explore the data locally or perform EDA before ingestion, check the notebook `notebooks/fathomnet-2025-cvpr-fgvc.ipynb`.

## Dataset Info

Source: [FathomNet 2025 - CVPR FGVC Competition](https://www.kaggle.com/competitions/fathomnet-2025/data)

- Type: Object Detection
- Classes: 79 (Marine species + supercategories)
- Format: COCO JSON
