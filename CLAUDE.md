# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FiftyOne Enterprise project for analyzing the FathomNet 2025 dataset (CVPR-FGVC marine species competition). The workflow involves streaming images from FathomNet URLs to GCS, then ingesting them into FiftyOne Enterprise for analysis.

## Build and Development Commands

```bash
# Create virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate
UV_EXTRA_INDEX_URL="https://<token>@pypi.fiftyone.ai" uv pip install -e .

# Upload images to GCS
python -m fathomnet_voxel51.upload_to_gcs [--limit N]

# Ingest dataset into FiftyOne
python -m fathomnet_voxel51.ingest_dataset [--recreate] [--limit N]

# Run pre-commit hooks manually
pre-commit run --all-files

# Install pre-commit hooks
pre-commit install
```

## Code Style

- Uses **Ruff** for linting and formatting (configured via pre-commit)
- Uses **Prettier** for YAML/JSON/Markdown formatting
- Pre-commit hooks auto-fix issues on commit

## Architecture

The main package (`fathomnet_voxel51/`) contains:

- `upload_to_gcs.py`: Async image streamer that uploads images from FathomNet URLs directly to GCS (no local disk I/O)
- `ingest_dataset.py`: Creates FiftyOne dataset from COCO JSON annotations, pointing to GCS image paths
- `check_gcp_auth.py`: Utility to verify GCP authentication

Data flow:

1. `upload_to_gcs.py`: Stream images from FathomNet URLs → GCS bucket
2. `ingest_dataset.py`: Read COCO JSON → Create FiftyOne samples with GCS paths → Tag with split (train/test)

## Required Environment Variables

```bash
FIFTYONE_API_URI="https://<deployment>.fiftyone.ai"
FIFTYONE_API_KEY="<api-key>"
GOOGLE_CLOUD_PROJECT="<gcp-project-id>"
```
