module "frontend" {
  source                = "./modules/cloud_run/"
  service_name          = "frontend"
  region                = var.region
  image                 = "gcr.io/google-samples/hello-app:1.0"
  port                  = 8080
  service_account_email = module.frontend_sa.service_account_email
  auth                  = "public"
  by_req                = true
  min_instances         = 0
  max_instances         = 3
  ingress               = "INGRESS_TRAFFIC_ALL"
  env_vars = {
    "BACK_END_API" = module.backend.cloud_run_endpoint
  }
  depends_on            = [
    module.backend,
    ]
}

module "backend" {
  source                = "./modules/cloud_run/"
  service_name          = "backend"
  region                = var.region
  image                 = "gcr.io/google-samples/hello-app:1.0"
  port                  = 8080
  service_account_email = module.backend_sa.service_account_email
  auth                  = "public"
  by_req                = true
  min_instances         = 0
  max_instances         = 3
  ingress               = "INGRESS_TRAFFIC_ALL"
  depends_on            = [
    ]
}