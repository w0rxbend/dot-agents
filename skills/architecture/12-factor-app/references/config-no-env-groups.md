---
title: Treat Environment Variables as Granular Controls Not Grouped Environments
impact: HIGH
impactDescription: scales to unlimited deploys, prevents combinatorial explosion
tags: config, environments, scaling, deployment
---

## Treat Environment Variables as Granular Controls Not Grouped Environments

Never group config into named "environments" (development, staging, production). Each env var is independent control, set per deploy.

**Incorrect (grouped environments):**

```python
# settings.py
ENVIRONMENTS = {
    'development': {
        'DEBUG': True,
        'DATABASE_URL': 'sqlite:///dev.db',
        'LOG_LEVEL': 'DEBUG',
    },
    'staging': {
        'DEBUG': False,
        'DATABASE_URL': 'postgresql://staging-db/app',
        'LOG_LEVEL': 'INFO',
    },
    'production': {
        'DEBUG': False,
        'DATABASE_URL': 'postgresql://prod-db/app',
        'LOG_LEVEL': 'WARNING',
    },
    # Need a new QA environment? Add 'qa' here.
    # Need joes-staging? Add 'joes_staging' here.
    # Combinatorial explosion!
}

env = os.environ.get('ENVIRONMENT', 'development')
config = ENVIRONMENTS[env]
```

**Correct (granular, independent env vars):**

```python
# settings.py
import os

# Each setting is independent
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
DATABASE_URL = os.environ['DATABASE_URL']
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
CACHE_TTL = int(os.environ.get('CACHE_TTL', '3600'))
FEATURE_NEW_UI = os.environ.get('FEATURE_NEW_UI', 'false').lower() == 'true'

# No predefined environments
# Each deploy sets exactly the values it needs
```

```bash
# Production
DATABASE_URL="postgresql://prod/app"
LOG_LEVEL="WARNING"
DEBUG="false"

# Staging
DATABASE_URL="postgresql://staging/app"
LOG_LEVEL="INFO"
DEBUG="false"

# Joe's personal staging
DATABASE_URL="postgresql://joe-staging/app"
LOG_LEVEL="DEBUG"
DEBUG="true"
FEATURE_NEW_UI="true"

# No code changes needed for new deploys
```

Reference: [The Twelve-Factor App - Config](https://12factor.net/config)
