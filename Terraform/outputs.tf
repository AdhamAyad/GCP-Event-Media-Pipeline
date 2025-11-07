output "frontend_api" {
    value = module.frontend.cloud_run_endpoint
}

output "backend_api" {
    value = module.backend.cloud_run_endpoint
}