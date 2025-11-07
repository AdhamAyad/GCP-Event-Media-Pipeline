resource "google_pubsub_subscription" "subscription" {
  name  = var.subscription_name
  topic = var.topic_name

  message_retention_duration = var.message_retention_duration
  ack_deadline_seconds       = var.ack_deadline_seconds

  retry_policy {
    minimum_backoff = var.retry_minimum_backoff
    maximum_backoff = var.retry_maximum_backoff
  }

  dead_letter_policy {
    dead_letter_topic     = var.dlt_topic_id
    max_delivery_attempts = var.max_delivery_attempts
  }

  push_config {
    push_endpoint = var.push_endpoint

    oidc_token {
      service_account_email = var.invoker_service_account_email
    }
  }
}