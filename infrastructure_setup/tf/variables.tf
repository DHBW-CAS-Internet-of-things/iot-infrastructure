# Define openstack password
variable "openstack_password" {
  description = "Password for OpenStack authentication"
  sensitive   = true
}
