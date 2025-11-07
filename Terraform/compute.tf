module "frontend" {
  source                = "./modules/cloud_run/"
  service_name          = "frontend"
  region                = var.region
  image                 = "gcr.io/google-samples/hello-app:1.0"
  port                  = 8080
  service_account_email = module.frontend_sa.service_account_email
  auth                  = "public"
  by_req                = true
  min_instances         = 0
  max_instances         = 3
  ingress               = "INGRESS_TRAFFIC_ALL"
  env_vars = {
    "BACK_END_API" = module.backend.cloud_run_endpoint
  }
  depends_on            = [
    module.backend,
    module.frontend_sa,
    ]
}

module "backend" {
  source                = "./modules/cloud_run/"
  service_name          = "backend"
  region                = var.region
  image                 = "gcr.io/google-samples/hello-app:1.0"
  port                  = 8080
  service_account_email = module.backend_sa.service_account_email
  auth                  = "public"
  by_req                = true
  min_instances         = 0
  max_instances         = 3
  ingress               = "INGRESS_TRAFFIC_ALL"
  env_vars = {
    "RAW_BUCKET_NAME" = google_storage_bucket.gcp_event_media.name
  }
  depends_on            = [
    google_storage_bucket.gcp_event_media,
    module.backend_sa,
    ]
}

module "media_thumbnail" {
  source                = "./modules/cloud_run/"
  service_name          = "media-thumbnail"
  region                = var.region
  image                 = "gcr.io/google-samples/hello-app:1.0"
  port                  = 8080
  service_account_email = module.media_thumbnail_sa.service_account_email
  auth                  = "private"
  by_req                = true
  min_instances         = 0
  max_instances         = 3
  ingress               = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  env_vars = {
    "RAW_BUCKET_NAME" = google_storage_bucket.gcp_event_media.name,
    "PROCESSED_BUCKET_NAME" = google_storage_bucket.gcp_event_media_processed_bucket.name
  }
  depends_on            = [
    google_storage_bucket.gcp_event_media,
    google_storage_bucket.gcp_event_media_processed_bucket,
    module.backend_sa,
    ]
}

module "media_display" {
  source                = "./modules/cloud_run/"
  service_name          = "media-display"
  region                = var.region
  image                 = "gcr.io/google-samples/hello-app:1.0"
  port                  = 8080
  service_account_email = module.media_display_sa.service_account_email
  auth                  = "private"
  by_req                = true
  min_instances         = 0
  max_instances         = 3
  ingress               = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  env_vars = {
    "RAW_BUCKET_NAME" = google_storage_bucket.gcp_event_media.name,
    "PROCESSED_BUCKET_NAME" = google_storage_bucket.gcp_event_media_processed_bucket.name
  }
  depends_on            = [
    google_storage_bucket.gcp_event_media,
    google_storage_bucket.gcp_event_media_processed_bucket,
    module.backend_sa,
    ]
}