# Define required providers
terraform {
required_version = ">= 0.14.0"
  required_providers {
    local = {
      source = "hashicorp/local"
    }
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 1.53.0"
    }
  }
}

# Configure the OpenStack Provider
provider "openstack" {
  user_name   = "pfisterer-cloud-lecture"
  password    = var.openstack_password
  domain_name = "default"
  auth_url    = "https://stack.dhbw.cloud:5000"
  tenant_id   = "a822c938ca2c4d4d9a41c28b42a44f40"
}

# Define nodes and flavors
locals {
  nodes = {
    "iot-node" = {
      flavor_id = "0ffe6506-ba05-4df1-9ce8-8197b57ce17b" # m1.extra_large
    }
  }
}

# Provision nodes
resource "openstack_compute_instance_v2" "vm" {
  for_each        = local.nodes
  name            = each.key
  image_id        = "c57c2aef-f74a-4418-94ca-d3fb169162bf" # Ubuntu 24.04 2025-01
  flavor_id       = each.value.flavor_id
  key_pair        = "a-dixon"
  security_groups = ["default"]

  network {
    name = "DHBW"
  }
}

output "master_ip" {
  value = openstack_compute_instance_v2.vm["iot-node"].access_ip_v4
}
