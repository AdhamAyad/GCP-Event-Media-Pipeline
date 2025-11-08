output "service_account_email" {
  value = google_service_account.service_account_module.email
}

output "name" {
  description = "The fully qualified name (ID) of the service account."
  value       = google_service_account.service_account_module.name
}