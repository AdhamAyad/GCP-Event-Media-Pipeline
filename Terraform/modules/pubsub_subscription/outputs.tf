output "name" {
  description = "The name of the created subscription."
  value       = google_pubsub_subscription.this.name
}

output "id" {
  description = "The full ID of the created subscription."
  value       = google_pubsub_subscription.this.id
}