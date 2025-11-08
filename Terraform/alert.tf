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
      filter = join(" AND ", [
        "resource.type = \"pubsub_topic\"",
        "metric.type = \"pubsub.googleapis.com/topic/send_request_count\"",
        "resource.label.\"topic_id\" = \"${google_pubsub_topic.dlt_topic.name}\""
      ])
      
      duration = "60s" 
      
      comparison = "COMPARISON_GT"
      threshold_value = 0 
      
      
      trigger {
        count = 1 
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email_channel.id
  ]
  
  documentation {
    content = "A message failed all retries (5 times) in one of the workshops (Thumbnail, Display, Metadata, or AI) and was sent to the Dead Letter Topic. The pipeline is blocked. Check the DLT Topic and the Cloud Run logs immediately."
    mime_type = "text/markdown"
  }
  
  depends_on = [
    google_monitoring_notification_channel.email_channel,
    google_pubsub_topic.dlt_topic
  ]
}