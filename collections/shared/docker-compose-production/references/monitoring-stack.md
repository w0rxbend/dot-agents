# Single-host monitoring stack (Prometheus, Grafana, Loki, Alloy)

Read this when adding metrics and log collection to a Compose deployment. Pin every image to a release you have checked; the `${...:?}` variables force that.

```yaml
services:
  prometheus:
    image: prom/prometheus:${PROMETHEUS_VERSION:?pin prometheus}
    restart: unless-stopped
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --storage.tsdb.retention.time=30d
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/alerts:/etc/prometheus/alerts:ro
      - prometheus-data:/prometheus
    networks: [monitoring]
    ports: ["127.0.0.1:9090:9090"]
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s

  grafana:
    image: grafana/grafana:${GRAFANA_VERSION:?pin grafana}
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_PASSWORD__FILE: /run/secrets/grafana_password
    secrets: [grafana_password]
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - grafana-data:/var/lib/grafana
    networks: [monitoring]
    ports: ["127.0.0.1:3001:3000"]      # publish through the reverse proxy with auth

  node-exporter:
    image: prom/node-exporter:${NODE_EXPORTER_VERSION:?pin node-exporter}
    restart: unless-stopped
    command: ["--path.rootfs=/host"]
    volumes: ["/:/host:ro,rslave"]
    pid: host
    network_mode: host                   # Prometheus scrapes host:9100

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:${CADVISOR_VERSION:?pin cadvisor}
    restart: unless-stopped
    privileged: true                     # required for full container metrics; keep it off public networks
    devices: [/dev/kmsg]
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro
    networks: [monitoring]

  loki:
    image: grafana/loki:${LOKI_VERSION:?pin loki}
    restart: unless-stopped
    command: -config.file=/etc/loki/config.yaml
    volumes:
      - ./monitoring/loki.yaml:/etc/loki/config.yaml:ro
      - loki-data:/loki
    networks: [monitoring]

  alloy:                                 # log shipper; replaces the deprecated Promtail
    image: grafana/alloy:${ALLOY_VERSION:?pin alloy}
    restart: unless-stopped
    command:
      - run
      - --server.http.listen-addr=0.0.0.0:12345
      - --storage.path=/var/lib/alloy/data
      - /etc/alloy/config.alloy
    volumes:
      - ./monitoring/config.alloy:/etc/alloy/config.alloy:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro   # read container logs; treat this container as privileged
      - alloy-data:/var/lib/alloy/data
    networks: [monitoring]

networks:
  monitoring: {}

volumes:
  prometheus-data: {}
  grafana-data: {}
  loki-data: {}
  alloy-data: {}

secrets:
  grafana_password: { file: ./secrets/grafana_password.txt }
```

## `monitoring/config.alloy`

```alloy
discovery.docker "containers" {
  host = "unix:///var/run/docker.sock"
}

discovery.relabel "containers" {
  targets = []
  rule {
    source_labels = ["__meta_docker_container_name"]
    regex         = "/(.*)"
    target_label  = "container"
  }
  rule {
    source_labels = ["__meta_docker_container_label_com_docker_compose_service"]
    target_label  = "service"
  }
}

loki.source.docker "containers" {
  host          = "unix:///var/run/docker.sock"
  targets       = discovery.docker.containers.targets
  relabel_rules = discovery.relabel.containers.rules
  forward_to    = [loki.write.default.receiver]
}

loki.write "default" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
  }
}
```

Component names and arguments can change between Alloy releases; check the docs for the pinned version, and run `alloy fmt` on the file to validate syntax.

## Verify

- Prometheus targets page shows node-exporter, cAdvisor and app targets as UP.
- In Grafana Explore, `{service="api"}` returns recent log lines from Loki.
- An alert rule fires when a test container is stopped.
