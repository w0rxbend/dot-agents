---
title: Store Configuration in Environment Variables
impact: CRITICAL
impactDescription: language-agnostic, impossible to accidentally commit, easy to change per deploy
tags: config, environment-variables, deployment, security
---

## Store Configuration in Environment Variables

Env vars change per deploy without code changes and rarely get committed by accident. Language-agnostic standard on every OS and cloud platform.

**Incorrect (config files not in version control):**

```yaml
# config/database.yml - not committed to git but...
production:
  host: prod-db.company.com
  password: secretpass

# Problems:
# 1. Easy to accidentally commit (one wrong .gitignore)
# 2. Different format per framework (YAML, JSON, INI, TOML)
# 3. Where does this file come from on fresh deploy?
# 4. How do you manage it across 50 servers?
```

**Correct (environment variables):**

```python
import os

# Works identically regardless of deployment platform
database_url = os.environ["DATABASE_URL"]
redis_url = os.environ["REDIS_URL"]
api_key = os.environ["API_KEY"]
```

```bash
# Set in shell
export DATABASE_URL="postgresql://user:pass@host/db"

# Or in Docker
docker run -e DATABASE_URL="..." myapp

# Or in Kubernetes
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: db-credentials
        key: url

# Or in Heroku/Railway/Render dashboard
# Or in AWS Systems Manager Parameter Store
# Or in GitHub Actions secrets
```

**Benefits:**
- Easy to rotate: change env var, restart app
- Works with secret management tools (Vault, AWS Secrets Manager)

Reference: [The Twelve-Factor App - Config](https://12factor.net/config)
