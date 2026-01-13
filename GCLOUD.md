# GCP Commands Reference

Common `gcloud` and `gsutil` commands for managing data in Google Cloud Storage.

## List Buckets and Objects

```bash
# List all buckets in your project
gsutil ls

# List objects in a bucket
gsutil ls gs://<your-bucket>/<your-dataset>/

# List with details (size, date)
gsutil ls -lh gs://<your-bucket>/<your-dataset>/
```

## View Storage Info

```bash
# Get total size of a folder
gsutil du -sh gs://<your-bucket>/<your-dataset>/

# Get bucket metadata
gsutil ls -L -b gs://<your-bucket>/
```

## Delete Data

```bash
# Delete a single object
gsutil rm gs://<your-bucket>/<your-dataset>/image.jpg

# Delete a folder recursively (use with caution!)
gsutil rm -r gs://<your-bucket>/<your-dataset>/

# Delete recursively with parallel operations (faster)
gsutil -m rm -r gs://<your-bucket>/<your-dataset>/

# Preview files before deleting (no dry-run flag available)
gsutil ls gs://<your-bucket>/<your-dataset>/
```

## Copy and Sync

```bash
# Copy local file to GCS
gsutil cp local_file.jpg gs://<your-bucket>/<your-dataset>/

# Copy from GCS to local
gsutil cp gs://<your-bucket>/<your-dataset>/image.jpg ./

# Sync a local directory to GCS (use -m for parallel transfers)
gsutil -m rsync -r ./local_dir/ gs://<your-bucket>/<your-dataset>/
```

> **Warning:** Delete operations are irreversible. Always double-check paths before running `gsutil rm -r`.
