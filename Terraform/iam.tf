module "frontend_sa" {
    source = "./modules/service_account"
    account_id = "frontend-sa"
    display_name = "Frontend Cloud Run Service Account"
    project_id = var.project_id
    rules = [
        "roles/run.invoker",
        "roles/artifactregistry.reader",
    ]
}

module "backend_sa" {
    source = "./modules/service_account"
    account_id = "backend-sa"
    display_name = "Backend Cloud Run Service Account"
    project_id = var.project_id
    rules = [
        "roles/run.invoker",
        "roles/artifactregistry.reader",
        "roles/storage.objectCreator",
    ]
}

resource "google_storage_bucket_iam_member" "backend_bucket_reader" {
  bucket = google_storage_bucket.gcp_event_media.name
  role   = "roles/storage.legacyBucketReader"
  member = "serviceAccount:${module.backend_sa.service_account_email}"
}

resource "google_storage_bucket_iam_member" "backend_bucket_creator" {
  bucket = google_storage_bucket.gcp_event_media.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${module.backend_sa.service_account_email}"
}

module "subscription_sa" {
    source = "./modules/service_account"
    account_id = "subscription-sa"
    display_name = "Subscription Service Account"
    project_id = var.project_id
    rules = [
        "roles/run.invoker",
    ]
}

module "media_thumbnail_sa" {
    source = "./modules/service_account"
    account_id = "media-thumbnail-sa"
    display_name = "mMdia Thumbnail Service Account"
    project_id = var.project_id
    rules = [
    ]
}

resource "google_storage_bucket_iam_member" "thumbnail_raw_bucket_reader" {
  bucket = google_storage_bucket.gcp_event_media.name
  role   = "roles/storage.legacyBucketReader"
  member = "serviceAccount:${module.media_thumbnail_sa.service_account_email}"
}

resource "google_storage_bucket_iam_member" "thumbnail_raw_object_viewer" {
  bucket = google_storage_bucket.gcp_event_media.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${module.media_thumbnail_sa.service_account_email}"
}

resource "google_storage_bucket_iam_member" "thumbnail_processed_bucket_reader" {
  bucket = google_storage_bucket.gcp_event_media_processed_bucket.name
  role   = "roles/storage.legacyBucketReader"
  member = "serviceAccount:${module.media_thumbnail_sa.service_account_email}"
}

resource "google_storage_bucket_iam_member" "thumbnail_processed_object_creator" {
  bucket = google_storage_bucket.gcp_event_media_processed_bucket.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${module.media_thumbnail_sa.service_account_email}"
}
