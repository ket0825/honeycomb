# This code is compatible with Terraform 4.25.0 and versions that are backwards compatible to 4.25.0.
# For information about validating this Terraform code, see https://developer.hashicorp.com/terraform/tutorials/gcp-get-started/google-cloud-platform-build#format-and-validate-the-configuration

resource "google_compute_instance" "honeycomb-instance" {
  boot_disk {
    auto_delete = false
    device_name = "honeycomb-instance"
    mode        = "READ_WRITE"
    source      = "projects/webserver-project-425817/zones/asia-northeast3-c/disks/honeycomb-instance-private"
  }

  can_ip_forward      = false
  deletion_protection = true
  enable_display      = false

  labels = {
    goog-ec-src = "vm_add-tf"
  }

  machine_type = "e2-standard-2"
  name         = "honeycomb-instance"

  network_interface {
    queue_count = 0
    stack_type  = "IPV4_ONLY"
    subnetwork  = "projects/webserver-project-425817/regions/asia-northeast3/subnetworks/honeycomb-private-subnet"
  }

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
    preemptible         = false
    provisioning_model  = "STANDARD"
  }

  service_account {
    email  = "899712886937-compute@developer.gserviceaccount.com"
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  shielded_instance_config {
    enable_integrity_monitoring = true
    enable_secure_boot          = false
    enable_vtpm                 = true
  }

  tags = ["allow-health-check", "http-server", "https-server", "lb-health-check"]
  zone = "asia-northeast3-c"
}
