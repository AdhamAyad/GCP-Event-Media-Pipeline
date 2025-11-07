variable "project_id" {
       type = string
       description = "Google Cloud project ID"
       default = "end-to-end-rag-application"
    }

variable "region" {
       type = string
       description = "Current Region"
       default = "us-east1"
    }

variable "gcp_event_media_name" {
       type = string
       description = "Bucket Name"
    }    