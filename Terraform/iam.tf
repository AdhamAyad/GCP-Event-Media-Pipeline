module "frontend_sa" {
    source = "./modules/service_account"
    account_id = "frontend-sa"
    display_name = "Frontend Cloud Run Service Account"
    project_id = var.project_id
    rules = [
        "roles/run.invoker",
        "roles/artifactregistry.reader",
    ]
}

module "backend_sa" {
    source = "./modules/service_account"
    account_id = "backend-sa"
    display_name = "Backend Cloud Run Service Account"
    project_id = var.project_id
    rules = [
        "roles/run.invoker",
        "roles/artifactregistry.reader",
        "roles/storage.objectCreator",
        "roles/storage.legacyBucketReader"
    ]
}