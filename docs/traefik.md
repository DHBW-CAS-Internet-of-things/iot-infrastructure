## Reverse Proxy mit Traefik

Traefik fungiert als Reverse Proxy vor den Services und übernimmt Routing, Pfad-Präfixe, und Port-Bindings. Dadurch bleiben die Container selbst unverändert (Standard-Ports), während Traefik Zugriffe sauber verteilt und Services unter konsistenten URLs bereitstellt.

### Basis-Konfiguration (Compose-Service `traefik`)

- Image: `traefik:v2.11`
- Docker Provider: aktiviert, `exposedbydefault=false` – nur Container mit `traefik.enable=true` werden veröffentlicht.
- EntryPoints:
  - `web`: Port 80 (HTTP, Subpfad-Routing für Web-UI Services)
  - `ha`: Port 8123 (Home Assistant, Root-Routing)
  - `influx`: Port 8086 (InfluxDB, Root-Routing)
- Ports: `80:80`, `8123:8123`, `8086:8086`
- Volume: `/var/run/docker.sock:ro` (liest Labels der Container)
- Dashboard ist standardmäßig deaktiviert (aus Sicherheitsgründen).

### Routing je Service (Labels)

Die folgenden Container definieren Traefik-Labels, die Regeln (Router), EntryPoints und optionale Middlewares festlegen.

#### n8n
- Pfad: `/n8n` (Subpfad)
- EntryPoint: `web`
- Middlewares: Redirect ohne Slash → mit Slash; StripPrefix `/n8n` vor Weiterleitung
- Ziel-Port: 5678
- Hinweis: Die URL-Generierung in n8n wird per `.env` gesteuert (N8N_PATH, N8N_EDITOR_BASE_URL, WEBHOOK_URL).

#### Grafana
- Pfad: `/grafana` (Subpfad)
- EntryPoint: `web`
- Middlewares: Redirect `/grafana` → `/grafana/`
- Ziel-Port: 3000
- Hinweis: Grafana ist für Subpfad-Betrieb konfiguriert (Root URL, Serve from sub path). Provisioning wird per Volume eingebunden (separat dokumentiert).

#### Web Audio Frontend
- Pfad: `/audio` (Subpfad)
- EntryPoint: `web`
- Middlewares: Redirect `/audio` → `/audio/`, StripPrefix `/audio`
- Ziel-Port: 80

#### Clap API
- Pfad: `/api` (Subpfad)
- EntryPoint: `web`
- Middlewares: StripPrefix `/api`
- Ziel-Port: 8000

#### InfluxDB
- Pfad: Root ("/") auf eigenem EntryPoint `influx`
- EntryPoint: `influx` (Port 8086)
- Ziel-Port: 8086

#### Home Assistant
- Pfad: Root ("/") auf eigenem EntryPoint `ha`
- EntryPoint: `ha` (Port 8123)
- Ziel-Port: 8123
- Hinweis: In `homeassistant_config/configuration.yaml` sind `use_x_forwarded_for: true` und ein `trusted_proxies` Netz gesetzt, damit Home Assistant korrekt hinter dem Proxy arbeitet.

### Betrieb

- Traefik wird automatisch mit Docker Compose gestartet und liest die Labels der Services ein.
- Nur Services mit `traefik.enable=true` sind extern erreichbar; alle anderen bleiben intern.
- Die Kombination aus EntryPoints und Pfad-Regeln ermöglicht klare Trennung: 
  - Subpfad-Services über `web` (Port 80),
  - Root-Services über dedizierte Ports/EntryPoints (`ha` und `influx`).
