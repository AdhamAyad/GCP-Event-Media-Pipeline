provider "google" {
      credentials = file("GCP-Event-Media-Pipeline.json") 
      project = var.project_id
      region = var.region
    }