## Provisionierung einer Node mit Terraform

Bevor die Software Komponenten, die für die Umsetzung der Use Cases benötigt werden, konfiguriert werden können, müssen diese auf einer zentralen Cloud Instanz deployed werden. Hierfür wird eine virtuelle Maschine im OpenStack Cluster der DHBW Mannheim verwendet.

Einem Infrastructure-as-Code (IaC) Ansatz folgend, wird diese virtuelle Maschine nicht über die Weboberfläche des OpenStack Clusters erstellt, sondern über Terraform provisioniert. Terraform erlaubt das deklarative Erstellen von VMs über Code-ähnliche Definition der Parameter. Hierdurch wird wiederholtes provisionieren und deprovisionieren der Ressourcen grundlegend vereinfacht und die Wiederholbarkeit maßgeblich verbessert.

Das Terraform Skript, das für das Erstellen der VM für den IoT Software Stack verwendet wurde, gliedert sich in zwei Teile:
1. Definition und Konfiguration des sog. Providers
2. Konfiguration und Provisionierung der VM

```YAML
# Define required providers
terraform {
	required_version = ">= 0.14.0"
	required_providers {
		openstack = {
			source = "terraform-provider-openstack/openstack"
			version = "~> 1.53.0"
		}
	}
} 

# Configure the OpenStack Provider
provider "openstack" {
	user_name = "pfisterer-cloud-lecture"
	password = var.openstack_password
	domain_name = "default"
	auth_url = "https://stack.dhbw.cloud:5000"
	tenant_id = "a822c938ca2c4d4d9a41c28b42a44f40"
}
```

Der obige Auszug aus dem Terraform Skript zeigt die Definition und Konfiguration des Terraform Providers. Dieser Provider ist die Schnittstelle zum OpenStack Cluster und erlaubt das Erstellen von Ressourcen (u.a. VMs).

Für den OpenStack Provider werden Benutzername und Passwort deklariert, über die die Anmeldung am Cluster gemacht wird. Das Passwort wird hierbei aus einer Umgebungsvariablen ausgelesen, damit es nicht im Skript in ein Git Repository eingecheckt wird.
Zusätzlich werden der Domain Name, die Authentifizierungs-URL, sowie die Tenant ID gesetzt. Diese Informationen werden benötigt, um sich am richtigen OpenStack Cluster zu authentifizieren und die Ressourcen im korrekten Tenant zu provisionieren.

```YAML
# Provision nodes
resource "openstack_compute_instance_v2" "vm" {
	name = "iot-node"
	image_id = "c57c2aef-f74a-4418-94ca-d3fb169162bf"
	flavor_id = "0ffe6506-ba05-4df1-9ce8-8197b57ce17b"
	key_pair = "a-dixon"
	security_groups = ["default"]
	
	network {
		name = "DHBW"
	}
}

output "master_ip" {
	value = openstack_compute_instance_v2.vm["iot-node"].access_ip_v4
}
```

Der obige Abschnitt zeigt die Definition und Provisionierung der VM im OpenStack Cluster. Für die VM werden der Name und das Betriebssystem-Image, in diesem Fall Ubuntu 24.04 2025-01 gesetzt. Zusätzlich werden das Flavor, d.h. die Art von VM, in diesem Fall eine VM vom Typ "m1.extra_large", sowie das SSH-Schlüsselpaar, die Sicherheitsgruppe und das verbundene Netzwerk gesetzt.

Nach Provisionierung der VM soll die IPv4 Adresse, die vom OpenStack Cluster allokiert wurde, ausgegeben werden, damit man sich für die weitere Konfiguration mit der VM verbinden kann.
