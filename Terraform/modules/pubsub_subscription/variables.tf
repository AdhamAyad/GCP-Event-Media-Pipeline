variable "subscription_name" {
  description = "The unique name for the subscription."
  type        = string
}

variable "topic_name" {
  description = "The name of the main topic to subscribe to."
  type        = string
}

variable "dlt_topic_id" {
  description = "The full ID of the Dead Letter Topic (DLT)."
  type        = string
}

variable "push_endpoint" {
  description = "The URL of the Cloud Run service (push endpoint)."
  type        = string
}

variable "invoker_service_account_email" {
  description = "The email of the SA used by Pub/Sub for OIDC authentication."
  type        = string
}

variable "ack_deadline_seconds" {
  description = "The acknowledgment deadline in seconds."
  type        = number
  default     = 180
}

variable "max_delivery_attempts" {
  description = "Number of failed attempts before sending to DLT."
  type        = number
  default     = 5
}

variable "message_retention_duration" {
  description = "How long to retain messages if the subscriber is offline."
  type        = string
  default     = "604800s" # 7 days
}

variable "retry_minimum_backoff" {
  description = "The minimum backoff time for the retry policy."
  type        = string
  default     = "5s"
}

variable "retry_maximum_backoff" {
  description = "The maximum backoff time for the retry policy."
  type        = string
  default     = "60s"
}