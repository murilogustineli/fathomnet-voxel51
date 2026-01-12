# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FiftyOne Enterprise project for analyzing the FathomNet 2025 dataset (CVPR-FGVC marine species competition). The workflow involves downloading images from FathomNet URLs, cropping ROIs from bounding box annotations, and preparing data for FiftyOne ingestion.

## Build and Development Commands

```bash
# Create virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate
uv pip install -e .

# Run the data download script
python -m fathomnet_voxel51.download_data <dataset_path> <output_dir> [-n NUM_DOWNLOADS] [-v|-vv]

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

The main package (`fathomnet-voxel51/`) contains:

- `download_data.py`: Async image downloader that processes COCO-format datasets, downloads images via httpx, crops ROIs using Pillow, and outputs annotations as CSV

Data flow:

1. Load COCO JSON annotations via `coco-lib`
2. Download images concurrently (semaphore-limited)
3. Crop each annotation's bounding box to create ROI images
4. Write path/label CSV for FiftyOne ingestion

## Required Environment Variables

```bash
FIFTYONE_API_URI="https://<deployment>.fiftyone.ai"
FIFTYONE_API_KEY="<api-key>"
GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcp_credentials.json"
```
