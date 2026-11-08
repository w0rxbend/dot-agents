---
title: Validate Required Configuration at Application Startup
impact: HIGH
impactDescription: fast failure prevents silent misconfiguration, improves debugging
tags: config, validation, startup, error-handling
---

## Validate Required Configuration at Application Startup

Fail fast and loudly if required config is missing or invalid. Check all required env vars at startup, before accepting traffic.

**Incorrect (late configuration failure):**

```python
import os

# No validation at startup
DATABASE_URL = os.environ.get('DATABASE_URL')  # Might be None

def get_user(user_id):
    # Fails here, possibly hours after startup
    # during a critical user request
    conn = connect(DATABASE_URL)  # TypeError: expected string, got None
    return conn.execute("SELECT * FROM users WHERE id = ?", user_id)
```

**Correct (early validation):**

```python
import os
import sys

class Config:
    def __init__(self):
        self.database_url = self._require('DATABASE_URL')
        self.redis_url = self._require('REDIS_URL')
        self.api_key = self._require('API_KEY')
        self.log_level = os.environ.get('LOG_LEVEL', 'INFO')
        self.debug = os.environ.get('DEBUG', 'false').lower() == 'true'

        # Validate format
        if not self.database_url.startswith(('postgresql://', 'mysql://')):
            self._fail('DATABASE_URL must be a valid database connection string')

    def _require(self, name):
        value = os.environ.get(name)
        if not value:
            self._fail(f'Required environment variable {name} is not set')
        return value

    def _fail(self, message):
        print(f'Configuration error: {message}', file=sys.stderr)
        sys.exit(1)

# Validate immediately at import time
config = Config()

# App only starts if all config is valid
def get_user(user_id):
    conn = connect(config.database_url)  # Always valid
    return conn.execute("SELECT * FROM users WHERE id = ?", user_id)
```

Reference: [The Twelve-Factor App - Config](https://12factor.net/config)
