import json
import asyncio
import aiohttp
import argparse
from google.cloud import storage
from tqdm.asyncio import tqdm_asyncio

# CONFIGURATION
BUCKET_NAME = "voxel51-test"


async def upload_stream(session, url, blob_name, bucket, semaphore):
    async with semaphore:
        blob = bucket.blob(blob_name)
        if blob.exists():
            return "skipped"

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    blob.upload_from_string(
                        content, content_type=response.headers.get("Content-Type")
                    )
                    return "uploaded"
                else:
                    return f"error_status_{response.status}"
        except Exception as e:
            return f"error_{str(e)}"


async def process_split(json_path, split_name, limit=None, concurrent=50):
    # 1. Setup GCS
    storage_client = storage.Client()  # Project inferred from auth
    bucket = storage_client.bucket(BUCKET_NAME)

    # Define prefix based on split (e.g., 'fathomnet/train_images/')
    gcp_prefix = f"fathomnet/{split_name}_images/"

    # 2. Load JSON
    print(f"Loading {json_path} for split '{split_name}'...")
    with open(json_path, "r") as f:
        data = json.load(f)

    images = data["images"]
    if limit:
        images = images[:limit]
        print(f"️Limiting to first {limit} images.")

    # 3. Async Stream
    semaphore = asyncio.Semaphore(concurrent)
    print(
        f"Stream-uploading {len(images)} images to gs://{BUCKET_NAME}/{gcp_prefix}..."
    )

    async with aiohttp.ClientSession() as session:
        tasks = []
        for img in images:
            # Filename safety: ensure it's clean
            fname = img["file_name"]
            blob_name = f"{gcp_prefix}{fname}"
            url = img["coco_url"]

            tasks.append(upload_stream(session, url, blob_name, bucket, semaphore))

        results = await tqdm_asyncio.gather(*tasks)

    # 4. Report
    print(
        f"Split '{split_name}' complete: {results.count('uploaded')} uploaded, {results.count('skipped')} skipped."
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
