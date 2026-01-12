import fiftyone as fo

# CONFIGURATION
BUCKET_URI = "gs://voxel51-test/fathomnet/images/"
DATASET_NAME = "fathomnet-2025"
JSON_PATH = "data/dataset_train.json"


def ingest():
    # Check if dataset exists
    if fo.dataset_exists(DATASET_NAME):
        print(f"Dataset {DATASET_NAME} already exists. Deleting and recreating...")
        fo.delete_dataset(DATASET_NAME)

    # Load the COCO Annotations
    print("Loading JSON annotations...")
    dataset = fo.Dataset.from_dir(
        dataset_type=fo.types.COCODetectionDataset,
        data_path=BUCKET_URI,  # Point data_path to the Cloud Bucket
        labels_path=JSON_PATH,  # Point labels to local JSON
        name=DATASET_NAME,
        label_types=["detections"],
        max_samples=None,
    )

    # Persistence
    dataset.persistent = True

    print(f"Successfully created dataset '{DATASET_NAME}' with {len(dataset)} samples.")
    print("The images remain in GCP, but FiftyOne now knows where to find them.")


if __name__ == "__main__":
    ingest()
