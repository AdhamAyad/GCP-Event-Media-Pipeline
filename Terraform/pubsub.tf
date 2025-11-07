resource "google_pubsub_topic" "bucket_events_topic" {
  name = "bucket-events-topic"
}

resource "google_pubsub_subscription" "media_thumbnail_sub" {
  name  = "media-thumbnail-sub"
  topic = google_pubsub_topic.bucket_events_topic.name

  message_retention_duration = "604800s"

  ack_deadline_seconds = 180

  retry_policy {
    minimum_backoff = "5s"
    maximum_backoff = "60s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dlt_topic.id
    max_delivery_attempts = 5
  }

  push_config {
    push_endpoint = module.media_thumbnail.cloud_run_endpoint

    oidc_token {
      service_account_email = module.subscription_sa.service_account_email
    }
  }

  depends_on = [
    google_pubsub_topic.bucket_events_topic,
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