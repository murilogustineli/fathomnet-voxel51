"""
Load FathomNet images to a GCP bucket.

This script streams images from their COCO URLs directly to Google Cloud Storage,
avoiding local disk I/O. It processes both train and test splits asynchronously.

PREREQUISITES:
    1. Authenticate with GCP:
        $ gcloud auth application-default login

    2. Ensure you have access to the target bucket (default: voxel51-test)

    3. Have the dataset JSON files in the data/ directory:
        - data/dataset_train.json
        - data/dataset_test.json

USAGE:
    # Run on the full dataset (all images):
        $ python -m fathomnet_voxel51.load_data_gcp

    # Run on a subset of 100 images (for testing):
        $ python -m fathomnet_voxel51.load_data_gcp --limit 100

    # Run with custom JSON paths:
        $ python -m fathomnet_voxel51.load_data_gcp --train_json path/to/train.json --test_json path/to/test.json

    # Run only on train split with 100 images:
        $ python -m fathomnet_voxel51.load_data_gcp --train_json data/dataset_train.json --test_json "" --limit 100

ARGUMENTS:
    --train_json : Path to training dataset JSON (default: data/dataset_train.json)
    --test_json  : Path to test dataset JSON (default: data/dataset_test.json)
    --limit      : Number of images to process per split (default: None = all images)
"""

import json
import asyncio
import aiohttp
import argparse
from gcloud.aio.storage import Storage
from google.cloud import storage as sync_storage
from tqdm.asyncio import tqdm_asyncio

# CONFIGURATION
BUCKET_NAME = "voxel51-test"


async def upload_stream(session, gcs_client, url, blob_name, existing_blobs, semaphore):
    """Upload a single image from URL to GCS (fully async)."""
    async with semaphore:
        # Skip if already exists (checked against pre-fetched set)
        if blob_name in existing_blobs:
            return "skipped"

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    content_type = response.headers.get("Content-Type", "image/jpeg")
                    await gcs_client.upload(
                        BUCKET_NAME,
                        blob_name,
                        content,
                        content_type=content_type,
                    )
                    return "uploaded"
                else:
                    return f"error_status_{response.status}"
        except Exception as e:
            return f"error_{str(e)}"


def fetch_existing_blobs(prefix):
    """Pre-fetch all existing blob names under a prefix (synchronous, runs once)."""
    print(f"Checking existing files in gs://{BUCKET_NAME}/{prefix}...")
    client = sync_storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs(prefix=prefix)
    existing = {blob.name for blob in blobs}
    print(f"Found {len(existing)} existing files.")
    return existing


async def process_split(json_path, split_name, limit=None, concurrent=50):
    """Process a dataset split: download images and upload to GCS."""
    # Define prefix based on split (e.g., 'fathomnet/train_images/')
    gcp_prefix = f"fathomnet/{split_name}_images/"

    # 1. Pre-fetch existing blobs (one API call instead of N)
    existing_blobs = fetch_existing_blobs(gcp_prefix)

    # 2. Load JSON
    print(f"Loading {json_path} for split '{split_name}'...")
    with open(json_path, "r") as f:
        data = json.load(f)

    images = data["images"]
    if limit:
        images = images[:limit]
        print(f"Limiting to first {limit} images.")

    # 3. Filter out already uploaded images early
    images_to_upload = [
        img for img in images if f"{gcp_prefix}{img['file_name']}" not in existing_blobs
    ]
    skipped_count = len(images) - len(images_to_upload)
    if skipped_count > 0:
        print(f"Skipping {skipped_count} already uploaded images.")

    if not images_to_upload:
        print(f"Split '{split_name}' complete: 0 uploaded, {skipped_count} skipped.")
        return

    # 4. Async Stream with truly async GCS client
    semaphore = asyncio.Semaphore(concurrent)
    print(
        f"Stream-uploading {len(images_to_upload)} images to gs://{BUCKET_NAME}/{gcp_prefix}..."
    )

    async with aiohttp.ClientSession() as session:
        async with Storage() as gcs_client:
            tasks = []
            for img in images_to_upload:
                fname = img["file_name"]
                blob_name = f"{gcp_prefix}{fname}"
                url = img["coco_url"]

                tasks.append(
                    upload_stream(
                        session, gcs_client, url, blob_name, existing_blobs, semaphore
                    )
                )

            results = await tqdm_asyncio.gather(*tasks)

    # 5. Report
    uploaded = results.count("uploaded")
    errors = len([r for r in results if r.startswith("error")])
    print(
        f"Split '{split_name}' complete: {uploaded} uploaded, {skipped_count} skipped, {errors} errors."
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_json", type=str, default="data/dataset_train.json")
    parser.add_argument("--test_json", type=str, default="data/dataset_test.json")
    parser.add_argument(
        "--limit", type=int, default=None, help="Process N images per split for testing"
    )
    args = parser.parse_args()

    # Run for Train
    if args.train_json:
        asyncio.run(process_split(args.train_json, "train", args.limit))

    # Run for Test
    if args.test_json:
        asyncio.run(process_split(args.test_json, "test", args.limit))


if __name__ == "__main__":
    main()
