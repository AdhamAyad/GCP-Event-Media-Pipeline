terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.1.1"
    }
  }

  backend "gcs" {
    bucket      = "gcp-event-media-pipeline"
    prefix      = "state/"
  }
}