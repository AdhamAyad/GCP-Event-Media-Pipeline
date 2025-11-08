resource "google_monitoring_notification_channel" "email_channel" {
  project      = var.project_id
  type         = "email"
  display_name = "Adham (Admin Email)" 
  
  labels = {
    email_address = "adhamayad000@gmail.com" 
  }
}

resource "google_monitoring_alert_policy" "dlt_alert" {
  project      = var.project_id
  display_name = "Critical Pipeline Failure (DLT)"
  combiner     = "OR"

  conditions {
    display_name = "Message received in Dead Letter Topic"

    condition_threshold {
      filter = "resource.type = \"pubsub_topic\" AND metric.type = \"pubsub.googleapis.com/topic/send_request_count\" AND resource.label.\"topic_id\" = \"${google_pubsub_topic.dlt_topic.name}\""
      
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_SUM"
      }

      trigger {
        count = 1
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.email_channel.id
  ]

  documentation {
    content   = "A message failed all retries and was sent to the DLT. Check Cloud Run / Pub/Sub logs immediately."
    mime_type = "text/markdown"
  }

  depends_on = [
    google_monitoring_notification_channel.email_channel,
    google_pubsub_topic.dlt_topic
  ]
}