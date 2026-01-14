"""
Ingest FathomNet dataset into FiftyOne Enterprise.

This script creates a FiftyOne dataset by:
1. Reading COCO JSON annotations for train and test splits
2. Constructing GCS paths for each image
3. Converting COCO bounding boxes to FiftyOne detections
4. Tagging samples with their split (train/test) for filtering

The images remain in GCS - only metadata is stored in FiftyOne.

PREREQUISITES:
    1. Images uploaded to GCS via upload_to_gcs.py
    2. FiftyOne credentials configured in .env:
        FIFTYONE_API_URI="https://<deployment>.fiftyone.ai"
        FIFTYONE_API_KEY="<api-key>"

USAGE:
    $ python -m fathomnet_voxel51.ingest_dataset

    # Recreate dataset (deletes existing):
    $ python -m fathomnet_voxel51.ingest_dataset --recreate

    # Test with a subset (10 samples per split):
    $ python -m fathomnet_voxel51.ingest_dataset --recreate --limit 10
"""

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import fiftyone as fo  # noqa: E402
from tqdm import tqdm  # noqa: E402

# CONFIGURATION
BUCKET_NAME = "voxel51-test"
DATASET_NAME = "fathomnet-2025"

# Project root directory (parent of fathomnet_voxel51/)
PROJECT_ROOT = Path(__file__).parent.parent

SPLITS = {
    "train": {
        "json_path": PROJECT_ROOT / "data/dataset_train.json",
        "gcs_prefix": f"gs://{BUCKET_NAME}/fathomnet/train_images/",
    },
    "test": {
        "json_path": PROJECT_ROOT / "data/dataset_test.json",
        "gcs_prefix": f"gs://{BUCKET_NAME}/fathomnet/test_images/",
    },
}


def load_coco_json(json_path: Path) -> dict:
    """Load and parse COCO JSON file."""
    with open(json_path, "r") as f:
        return json.load(f)


def coco_bbox_to_fiftyone(bbox: list, img_width: int, img_height: int) -> list:
    """
    Convert COCO bbox [x, y, width, height] (pixels) to
    FiftyOne format [x, y, width, height] (normalized 0-1).
    """
    x, y, w, h = bbox
    return [
        x / img_width,
        y / img_height,
        w / img_width,
        h / img_height,
    ]


def create_samples_from_split(
    split_name: str, config: dict, limit: int | None = None
) -> list[fo.Sample]:
    """
    Create FiftyOne samples from a COCO JSON split.

    Args:
        split_name: Name of the split (train/test)
        config: Dict with json_path and gcs_prefix
        limit: Maximum number of samples to process (None = all)

    Returns:
        List of FiftyOne samples
    """
    json_path = config["json_path"]
    gcs_prefix = config["gcs_prefix"]

    if not Path(json_path).exists():
        print(f"Warning: {json_path} not found, skipping {split_name} split")
        return []

    print(f"Loading {json_path}...")
    data = load_coco_json(json_path)

    # Build lookup tables
    categories = {cat["id"]: cat["name"] for cat in data["categories"]}
    images_list = data["images"]
    if limit:
        images_list = images_list[:limit]
        print(f"  Limiting to {limit} samples")
    images = {img["id"]: img for img in images_list}

    # Group annotations by image_id
    annotations_by_image: dict[int, list] = {}
    for ann in data["annotations"]:
        img_id = ann["image_id"]
        if img_id not in annotations_by_image:
            annotations_by_image[img_id] = []
        annotations_by_image[img_id].append(ann)

    samples = []
    for img_id, img_data in tqdm(images.items(), desc=f"Processing {split_name}"):
        # Construct GCS filepath
        filepath = f"{gcs_prefix}{img_data['file_name']}"

        # Create sample
        sample = fo.Sample(filepath=filepath)

        # Add metadata
        sample["split"] = split_name
        sample["image_id"] = img_id
        sample["width"] = img_data["width"]
        sample["height"] = img_data["height"]
        if "date_captured" in img_data:
            sample["date_captured"] = img_data["date_captured"]

        # Add detections (if annotations exist for this image)
        detections = []
        for ann in annotations_by_image.get(img_id, []):
            bbox = coco_bbox_to_fiftyone(
                ann["bbox"], img_data["width"], img_data["height"]
            )
            label = categories.get(ann["category_id"], "unknown")

            detection = fo.Detection(
                label=label,
                bounding_box=bbox,
            )
            # Store original COCO annotation ID
            detection["annotation_id"] = ann["id"]
            detections.append(detection)

        sample["ground_truth"] = fo.Detections(detections=detections)

        # Tag for filtering in FiftyOne App
        sample.tags.append(split_name)

        samples.append(sample)

    return samples


def ingest(recreate: bool = False, limit: int | None = None):
    """Main ingestion function."""
    # Check if dataset exists
    if fo.dataset_exists(DATASET_NAME):
        if recreate:
            print(f"Deleting existing dataset '{DATASET_NAME}'...")
            fo.delete_dataset(DATASET_NAME)
        else:
            print(
                f"Dataset '{DATASET_NAME}' already exists. Use --recreate to replace."
            )
            return

    # Create new dataset on FiftyOne
    print(f"Creating dataset '{DATASET_NAME}'...")
    dataset = fo.Dataset(name=DATASET_NAME)

    # Process each split
    all_samples = []
    for split_name, config in SPLITS.items():
        samples = create_samples_from_split(split_name, config, limit=limit)
        all_samples.extend(samples)
        print(f"  {split_name}: {len(samples)} samples")

    # Add all samples to dataset
    print(f"Adding {len(all_samples)} samples to dataset...")
    dataset.add_samples(all_samples)

    # Make persistent
    dataset.persistent = True

    print(f"\nSuccessfully created dataset '{DATASET_NAME}'")
    print(f"Total samples: {len(dataset)}")
    print(f"Train samples: {len(dataset.match_tags('train'))}")
    print(f"Test samples: {len(dataset.match_tags('test'))}")
    print("\nImages remain in GCS. Filter by 'split' field or tags in the App.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the dataset if it already exists",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit samples per split for testing (default: all)",
    )
    args = parser.parse_args()

    ingest(recreate=args.recreate, limit=args.limit)


if __name__ == "__main__":
    main()
