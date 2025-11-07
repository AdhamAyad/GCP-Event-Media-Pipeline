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
  member = module.backend_sa.service_account_email 
}

resource "google_storage_bucket_iam_member" "backend_bucket_creator" {
  bucket = google_storage_bucket.gcp_event_media.name
  role   = "roles/storage.objectCreator"
  member = module.backend_sa.service_account_email
}