---
title: Export Services via Port Binding Using PORT Environment Variable
impact: MEDIUM
impactDescription: enables platform-managed port assignment, essential for container orchestration
tags: port, binding, environment, containers
---

## Export Services via Port Binding Using PORT Environment Variable

Twelve-factor app exports its service by binding to a port the environment specifies (typically the PORT variable). Execution environment (Kubernetes, Heroku, Docker) then assigns ports dynamically and routes traffic.

**Incorrect (hardcoded port):**

```python
# Port hardcoded - can't run multiple instances on same host
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    # What if port 8080 is taken?
    # How does Heroku/Railway tell the app which port to use?
```

```javascript
// Port hardcoded in code
const PORT = 3000;  // Always 3000, no flexibility
server.listen(PORT);
```

**Correct (port from environment):**

```python
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
    # Platform sets PORT, app obeys
    # Default 8080 for local development
```

```javascript
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Listening on port ${PORT}`);
});
```

```go
port := os.Getenv("PORT")
if port == "" {
    port = "8080"
}
http.ListenAndServe(":"+port, nil)
```

**How platforms use PORT:**

```bash
# Heroku sets PORT automatically
# Your Procfile just specifies the command
web: gunicorn app:app

# Kubernetes - port exposed in container spec
spec:
  containers:
  - name: app
    env:
    - name: PORT
      value: "8080"
    ports:
    - containerPort: 8080

# Docker - map host port to container port
docker run -e PORT=8080 -p 80:8080 myapp
# External port 80 → Container port 8080

# Docker Compose - multiple instances
services:
  app:
    environment:
      - PORT=8080
    deploy:
      replicas: 3
    # Load balancer routes to any replica's 8080
```

Reference: [The Twelve-Factor App - Port Binding](https://12factor.net/port-binding)
