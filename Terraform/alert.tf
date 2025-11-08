resource "google_monitoring_notification_channel" "email_channel" {
  project      = var.project_id
  type         = "email"
  display_name = "Adham (Admin Email)" 
  
  labels = {
    email_address = "adhamayad000@gmail.com" 
  }
}