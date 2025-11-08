resource "google_pubsub_topic" "bucket_events_topic" {
  name = "bucket-events-topic"
}

module "media_thumbnail_sub" {
  source = "./modules/pubsub_subscription" 

  subscription_name           = "media-thumbnail-sub"
  topic_name                  = google_pubsub_topic.bucket_events_topic.name
  dlt_topic_id                = google_pubsub_topic.dlt_topic.id
  push_endpoint               = module.media_thumbnail.cloud_run_endpoint
  invoker_service_account_email = module.subscription_sa.service_account_email

  depends_on = [
    module.media_thumbnail,
    module.subscription_sa
  ]
}

module "media_display_sub" {
  source = "./modules/pubsub_subscription" 

  subscription_name           = "media-display-sub"
  topic_name                  = google_pubsub_topic.bucket_events_topic.name
  dlt_topic_id                = google_pubsub_topic.dlt_topic.id
  push_endpoint               = module.media_display.cloud_run_endpoint
  invoker_service_account_email = module.subscription_sa.service_account_email

  depends_on = [
    module.media_display,
    module.subscription_sa
  ]
}

module "metadata_sub" {
  source = "./modules/pubsub_subscription" 

  subscription_name           = "metadata-sub"
  topic_name                  = google_pubsub_topic.bucket_events_topic.name
  dlt_topic_id                = google_pubsub_topic.dlt_topic.id
  push_endpoint               = module.metadata.cloud_run_endpoint
  invoker_service_account_email = module.subscription_sa.service_account_email

  depends_on = [
    module.metadata,
    module.subscription_sa
  ]
}

module "ai_labeling_sub" {
  source = "./modules/pubsub_subscription" 

  subscription_name           = "ai-labeling-sub"
  topic_name                  = google_pubsub_topic.bucket_events_topic.name
  dlt_topic_id                = google_pubsub_topic.dlt_topic.id
  push_endpoint               = module.ai_labeling.cloud_run_endpoint
  invoker_service_account_email = module.subscription_sa.service_account_email
  ack_deadline_seconds = 240

  depends_on = [
    module.ai_labeling,
    module.subscription_sa
  ]
}

resource "google_storage_notification" "bucket_uploads" {
  bucket         = google_storage_bucket.gcp_event_media.name
  payload_format = "JSON_API_V1"
  topic          = google_pubsub_topic.bucket_events_topic.id

  event_types = [
    "OBJECT_FINALIZE"
  ]

  depends_on = [
    google_pubsub_topic_iam_member.gcs_pubsub_publisher
    ]
}

resource "google_pubsub_topic" "dlt_topic" {
  name = "dlt-topic"
}