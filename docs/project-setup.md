## Projekt Setup mit Docker Compose

Das Projekt wird als Container-Stack mit Docker Compose betrieben. Im Zentrum stehen die Kernservices für Visualisierung, Datenhaltung und Systemintegration. Die Konfiguration ist weitgehend über `.env` parametrisiert und bindet zusätzliche Konfigurationsdateien via Volume-Mounts ein.

Hinweis: Das Traefik-Setup sowie die beiden Services für die Clap Recognition werden in separaten Dokumenten behandelt und sind hier bewusst ausgeklammert.

### .env Parameter (Auszug)

- PUBLIC_IP: Öffentliche IP der Node, wird u. a. von n8n zur URL-Generierung verwendet.
- N8N_USER / N8N_PASSWORD: Basis-Authentifizierung für den n8n Editor.
- GRAFANA_USER / GRAFANA_PASSWORD: Initiale Admin-Credentials für Grafana.
- INFLUXDB_INIT_MODE, INFLUXDB_ADMIN_USERNAME, INFLUXDB_ADMIN_PASSWORD, INFLUXDB_ORG, INFLUXDB_BUCKET, INFLUXDB_TOKEN: Initial-Setup und Zugriffstoken für InfluxDB 2.x.
- TELEGRAF_MQTT_*: Verbindungs- und Topic-Parameter für die MQTT-Integration in Telegraf.

### Services (Compose)

#### n8n (Workflow Automation)

- Image: `n8nio/n8n:latest`
- Authentifizierung und Pfadprefix werden über `.env` bzw. feste Werte gesetzt:
  - N8N_PATH=/n8n, N8N_EDITOR_BASE_URL=http://${PUBLIC_IP}/n8n, WEBHOOK_URL=http://${PUBLIC_IP}/n8n/
  - N8N_BASIC_AUTH_ACTIVE=true mit N8N_USER und N8N_PASSWORD aus `.env`
  - Optionale Härtung: N8N_DIAGNOSTICS_ENABLED=false, N8N_SECURE_COOKIE=false
- Persistenz: `./n8n_data:/home/node/.n8n`
- Hinweis: Routing erfolgt über den Reverse Proxy, Details siehe Traefik-Dokumentation (separat).

#### Grafana (Visualisierung)

- Image: `grafana/grafana:latest`
- Persistenz und Provisionierung via Volumes:
  - Daten: `./grafana_data:/var/lib/grafana`
  - Provisioning: `./grafana/provisioning:/etc/grafana/provisioning`
- Wichtige Umgebungsvariablen (aus `.env`):
  - INFLUXDB_TOKEN (für vordefinierte Datasource)
  - GF_SECURITY_ADMIN_USER, GF_SECURITY_ADMIN_PASSWORD
  - GF_SERVER_ROOT_URL="%(protocol)s://%(domain)s/grafana/", GF_SERVER_SERVE_FROM_SUB_PATH=true
  - Optional: Anonyme Anzeige aktiviert (GF_AUTH_ANONYMOUS_ENABLED=true, Org-Rolle Viewer), Login-Form deaktiviert
- Hinweis: Die eigentliche Provisionierungs- und Dashboard-Konfiguration liegt im gemounteten Provisioning-Verzeichnis und wird in einer separaten Dokumentation erläutert.

#### InfluxDB (Zeitreihendatenbank)

- Image: `influxdb:latest`
- Persistenz: `./influxdb_data:/var/lib/influxdb2`
- Initiale Einrichtung über `.env` Werte:
  - DOCKER_INFLUXDB_INIT_MODE=${INFLUXDB_INIT_MODE}
  - DOCKER_INFLUXDB_INIT_USERNAME=${INFLUXDB_ADMIN_USERNAME}
  - DOCKER_INFLUXDB_INIT_PASSWORD=${INFLUXDB_ADMIN_PASSWORD}
  - DOCKER_INFLUXDB_INIT_ORG=${INFLUXDB_ORG}
  - DOCKER_INFLUXDB_INIT_BUCKET=${INFLUXDB_BUCKET}
  - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=${INFLUXDB_TOKEN}
- Hinweis: Der HTTP-Zugriff wird über den Reverse Proxy bereitgestellt; Details zu Routing separat.

#### Telegraf (Daten-Ingest)

- Image: `telegraf:latest`
- Konfiguration per Read-Only Volume: `./telegraf/telegraf.conf:/etc/telegraf/telegraf.conf:ro`
- Parameter via `.env` für MQTT und InfluxDB:
  - TELEGRAF_MQTT_SERVER, TELEGRAF_MQTT_TOPIC_CLIMATE, TELEGRAF_MQTT_TOPIC_LIGHT
  - TELEGRAF_MQTT_USERNAME, TELEGRAF_MQTT_PASSWORD
  - INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET
- Hinweis: Die konkrete Telegraf-Konfiguration (Input-/Output-Plugins, MQTT-Topics etc.) ist im gemounteten Config-File definiert und wird separat dokumentiert.

#### Home Assistant

- Image: `ghcr.io/home-assistant/home-assistant:stable`
- Persistenz/Config: `./homeassistant_config:/config`
- Zeitsynchronisation: `/etc/localtime:/etc/localtime:ro`
- Relevante Einstellungen in `homeassistant_config/configuration.yaml` (Auszug):
  - `external_url` / `internal_url` auf die Node-IP (Port 8123)
  - HTTP Proxy-Integration: `use_x_forwarded_for: true` und `trusted_proxies: 172.16.0.0/12`
- Hinweis: Dieses Setup erlaubt den Betrieb hinter einem Reverse Proxy; Details zum Proxy-Routing befinden sich in der Traefik-Doku.

### Ausführung

- Compose im Projektverzeichnis starten (nachdem `.env` befüllt ist und Verzeichnisse/Volumes existieren):
  - Dienste starten: `docker compose up -d`
  - Status prüfen: `docker compose ps`

Hinweis zum Fokus: Diese Dokumentation konzentriert sich auf das Zusammenspiel der Kernservices und deren Einbindung über `.env` sowie Volumes. Konkrete Konfigurationsinhalte (Grafana Provisioning, Telegraf Pipelines) und der Reverse Proxy werden separat erläutert, um den Fokus auf die wesentlichen Betriebsparameter und Schnittstellen zu wahren.
