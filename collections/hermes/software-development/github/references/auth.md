# GitHub Authentication Setup

Two paths:

- **`git` (always available)** — HTTPS personal access tokens or SSH keys
- **`gh` CLI (if installed)** — richer GitHub API access, simpler auth flow

## Detection Flow

When user asks for GitHub work, run this check first:

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"

# Check if already authenticated
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"
```

**Decision tree:**
1. `gh auth status` shows authenticated: use `gh` for everything
2. `gh` installed but not authenticated: use "gh auth" method below
3. `gh` not installed: use "git-only" method below (no sudo needed)

---

## Method 1: Git-Only Authentication (No gh, No sudo)

### Option A: HTTPS with Personal Access Token (Recommended)

**Step 1: Create personal access token**

Send user to: **https://github.com/settings/tokens**

- Prefer **Fine-grained tokens** (sidebar there), limited to needed repos and permissions; classic fallback below
- Click "Generate new token (classic)"
- Name it, e.g. "hermes-agent"
- Select scopes:
  - `repo` (full repository access — read, write, push, PRs)
  - `workflow` (trigger and manage GitHub Actions)
  - `read:org` (for organization repos)
- Set expiration (90 days good default)
- Copy token now; it won't be shown again

**Step 2: Configure git to store token**

```bash
# Prefer an OS keychain helper: osxkeychain (macOS), manager (Windows), libsecret (Linux).
# Fallback "store" saves to ~/.git-credentials in plaintext (simple, persistent)
git config --global credential.helper store

# Now do a test operation that triggers auth — git will prompt for credentials
# Username: <their-github-username>
# Password: <paste the personal access token, NOT their GitHub password>
git ls-remote https://github.com/<their-username>/<any-repo>.git
```

**Alternative: cache helper (credentials expire from memory)**

```bash
# Cache in memory for 8 hours (28800 seconds) instead of saving to disk
git config --global credential.helper 'cache --timeout=28800'
```

**Avoid: token in remote URL** (`https://<user>:<token>@github.com/...`). Stored plaintext in `.git/config`, leaks via `git remote -v` and logs. Use a credential helper or `gh auth setup-git`.

**Step 3: Configure git identity**

```bash
# Required for commits — set name and email
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

**Step 4: Verify**

```bash
# Test push access (this should work without any prompts now)
git ls-remote https://github.com/<their-username>/<any-repo>.git

# Verify identity
git config --global user.name
git config --global user.email
```

### Option B: SSH Key Authentication

For users who prefer SSH or already have keys.

**Step 1: Check for existing SSH keys**

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || echo "No SSH keys found"
```

**Step 2: Generate key if needed**

```bash
# Generate an ed25519 key (modern, secure, fast). User runs it interactively to set
# a passphrase; never overwrite an existing key (Step 1).
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519

# Display the public key for them to add to GitHub
cat ~/.ssh/id_ed25519.pub
```

User adds public key at: **https://github.com/settings/keys**
- Click "New SSH key"
- Paste public key
- Title it, e.g. "hermes-agent-<machine-name>"

**Step 3: Test connection**

```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

**Step 4: Configure git to use SSH for GitHub**

```bash
# Rewrite HTTPS GitHub URLs to SSH automatically
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

**Step 5: Configure git identity**

```bash
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

---

## Method 2: gh CLI Authentication

`gh` handles both API access and git credentials in one step.

### Interactive Browser Login (Desktop)

> **PITFALL (agent-driven sessions on Windows):** driving `gh auth login` through pty background process, answer prompts with `process(submit)`, never `process(write)` with bare `\n`. On Windows PTY (ConPTY/pywinpty), Enter is carriage return; lone `\n` is not delivered as line terminator. So gh's "Press Enter to open the browser" prompt (blocking line read) never returns, and login hangs silently. From background session, browser may not open on user's desktop. If user reports that, fall back to device flow below.

```bash
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser
```

### Manual OAuth Device Flow (no TTY needed — PROVEN)

Fallback when interactive login impractical (agent-driven sessions, no browser launch, headless). Uses gh's public OAuth client id. User enters code at github.com/login/device. Scopes: `repo,read:org,gist` is documented minimum for `gh auth login --with-token`. Append `,workflow` only to push workflow files.

```bash
# 1. Request a device code (gh's official client_id)
RESP=$(curl -s -X POST -H "Accept: application/json" \
  -d "client_id=178c6fc778ccc68e1d6a&scope=repo,read:org,gist" \
  https://github.com/login/device/code)
DEVICE_CODE=$(echo "$RESP" | sed 's/.*"device_code":"\([^"]*\)".*/\1/')
USER_CODE=$(echo "$RESP" | sed 's/.*"user_code":"\([^"]*\)".*/\1/')
INTERVAL=$(echo "$RESP" | sed 's/.*"interval":\([0-9]*\).*/\1/'); INTERVAL=${INTERVAL:-5}
echo "Tell the user: go to https://github.com/login/device and enter code: $USER_CODE"

# 2. Poll for the token (respect interval; +5s on slow_down; ~15 min expiry).
#    Run this loop as a background process and show the user the code first.
while true; do
  sleep "$INTERVAL"
  POLL=$(curl -s -X POST -H "Accept: application/json" \
    -d "client_id=178c6fc778ccc68e1d6a&device_code=${DEVICE_CODE}&grant_type=urn:ietf:params:oauth:grant-type:device_code" \
    https://github.com/login/oauth/access_token)
  case "$POLL" in
    *access_token*)
      # Never echo the token; pipe it straight into gh.
      # timeout guards the headless-keyring hang (see pitfall below) —
      # on exit 124, fall back to writing ~/.config/gh/hosts.yml directly.
      echo "$POLL" | sed 's/.*"access_token":"\([^"]*\)".*/\1/' | timeout 20 gh auth login --with-token \
        || { echo "WITH_TOKEN_HUNG_OR_FAILED — use the hosts.yml fallback below"; exit 1; }
      gh auth setup-git
      gh auth status
      echo "LOGIN_COMPLETE"; break ;;
    *authorization_pending*) ;;                      # keep polling
    *slow_down*) INTERVAL=$((INTERVAL + 5)) ;;       # back off per GitHub docs
    *expired_token*) echo "CODE_EXPIRED — restart the flow"; exit 1 ;;
    *access_denied*) echo "USER_DENIED"; exit 1 ;;
    *) echo "UNEXPECTED: $POLL"; exit 1 ;;
  esac
done
```

Note: Windows winget installs put gh at `/c/Program Files/GitHub CLI`. Add to PATH in same shell: `export PATH="$PATH:/c/Program Files/GitHub CLI"`.

> **PITFALL (headless Linux): `gh auth login --with-token` can hang forever.**
> On keyring-less/headless boxes (VPS, containers, no dbus session), gh's
> credential storage may block indefinitely on secret-service keyring,
> even with `--insecure-storage`, silently. If command doesn't return
> within ~20s (detect by wrapping in `timeout 20 …`), skip gh's login
> machinery and write credential store directly:
>
> ```bash
> # $TOKEN = the access token from the device flow above (never echo it)
> mkdir -p ~/.config/gh
> install -m 600 /dev/null ~/.config/gh/hosts.yml   # private before token is written
> LOGIN=$(curl -s -H "Authorization: token $TOKEN" https://api.github.com/user \
>   | sed 's/.*"login": *"\([^"]*\)".*/\1/')
> printf 'github.com:\n    users:\n        %s:\n            oauth_token: %s\n    git_protocol: https\n    oauth_token: %s\n    user: %s\n' \
>   "$LOGIN" "$TOKEN" "$TOKEN" "$LOGIN" > ~/.config/gh/hosts.yml
> chmod 600 ~/.config/gh/hosts.yml
> gh auth status          # reads hosts.yml directly — verifies without the keyring
> gh auth setup-git       # wires the git credential helper (does not hang)
> ```
>
> `gh auth status` and `setup-git` read file store without touching
> keyring, so they work immediately. Proven on headless x86_64 VPS
> (gh 2.97.0, Aug 2026) after `--with-token` hung twice.

### Token-Based Login (Headless / SSH Servers)

```bash
# User runs this in their own shell (token file chmod 600, delete after).
# Never ask user to paste the token into chat.
gh auth login --with-token < ~/gh-token.txt

# Set up git credentials through gh
gh auth setup-git
```

If `--with-token` hangs here, use hosts.yml fallback from pitfall above.

### Verify

```bash
gh auth status
```

---

## Using the GitHub API Without gh

Without `gh`, `curl` plus personal access token reaches full GitHub API.

### Setting the Token for API Calls

```bash
# Option 1: env var (preferred). User sets it in own shell or ~/.hermes/.env; keeps it out of chat and argv
export GITHUB_TOKEN="<token>"

# Then use in curl calls:
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

### Extracting the Token from Git Credentials

If git credentials already configured (via credential.helper store), extract token:

```bash
# Read from git credential store: capture only; never run bare or echo it
export GITHUB_TOKEN=$(python3 -I "$GH_SKILL_DIR/scripts/git-credential-token.py")
```

### Helper: Detect Auth Method

Use at start of any GitHub workflow:

```bash
# Try gh first, fall back to git + curl
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  echo "AUTH_METHOD=gh"
elif [ -n "$GITHUB_TOKEN" ]; then
  echo "AUTH_METHOD=curl"
elif _hermes_env="${HERMES_HOME:-$HOME/.hermes}/.env"; [ -f "$_hermes_env" ] && grep -q "^GITHUB_TOKEN=" "$_hermes_env"; then
  export GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "$_hermes_env" | head -1 | cut -d= -f2 | tr -d '\n\r')
  echo "AUTH_METHOD=curl"
elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
  export GITHUB_TOKEN=$(python3 -I "$GH_SKILL_DIR/scripts/git-credential-token.py")
  echo "AUTH_METHOD=curl"
else
  echo "AUTH_METHOD=none"
  echo "Need to set up authentication first"
fi
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | GitHub disabled password auth. Use personal access token as password, or switch to SSH |
| `remote: Permission to X denied` | Token may lack `repo` scope. Regenerate with correct scopes |
| `fatal: Authentication failed` | Cached credentials may be stale. Run `git credential reject`, then re-authenticate |
| `ssh: connect to host github.com port 22: Connection refused` | Try SSH over HTTPS port: add `Host github.com` with `Port 443` and `Hostname ssh.github.com` to `~/.ssh/config` |
| Credentials not persisting | Check `git config --global credential.helper`: must be set (OS keychain helper, `store` or `cache`) |
| Multiple GitHub accounts | SSH with different keys per host alias in `~/.ssh/config`, or per-repo credential URLs |
| `gh: command not found` + no sudo | Use git-only Method 1 above; no installation needed |
