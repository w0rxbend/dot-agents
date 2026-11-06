# Private registry setup for Render

Render pulls private images through **Registry Credentials** from Dashboard, referenced in Blueprint YAML via `registryCredential.fromRegistryCreds`.

## Dashboard: Registry Credentials

1. In Render Dashboard, open **Registry Credentials** (or your team’s equivalent settings).
2. Create credential with memorable name (used in `render.yaml`).
3. Store **only** what registry expects (username + token, or cloud keys as required).

Blueprint reference pattern:

```yaml
services:
  - type: web
    name: api
    runtime: image
    image:
      url: docker.io/myorg/api:v1.2.3
    registryCredential:
      fromRegistryCreds:
        name: my-dockerhub-cred
```

Same `registryCredential` block works for `runtime: docker` with private Dockerfile base image.

---

## Docker Hub

- **Username:** Docker Hub user or org name.
- **Password / token:** personal access token (preferred) or account password.
- **Image URL examples:** `docker.io/myuser/myrepo:1.0.0`, or `myuser/myrepo@sha256:...` for immutability.

---

## GitHub Container Registry (GHCR)

- **Username:** GitHub username (or `x-access-token` patterns if registry documents them).
- **Password:** GitHub personal access token with at least `read:packages` (plus repo access if package is private to a repo).
- **Image URL:** `ghcr.io/OWNER/IMAGE:tag` or digest form.

---

## AWS Elastic Container Registry (ECR)

- **Registry URL is regional:** `ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/repository:tag`.
- **Authentication:** IAM user or role access keys with `ecr:GetAuthorizationToken` and repository pull permissions, **or** org-approved long-lived credentials. Render’s Dashboard form expects values Render documents for ECR (access key id + secret). Confirm field names when creating credential.
- **Important:** each region has own registry host. Image URL must match image’s region.

---

## Google Artifact Registry

- **Host:** `REGION-docker.pkg.dev/PROJECT/REPOSITORY/IMAGE:tag`.
- **Credential:** typically service account JSON key with **Artifact Registry Reader** on target repo (exact Dashboard fields follow Render’s registry UI).
- Prefer service accounts over user passwords for CI-style pulls.

---

## Blueprint: `runtime: image`

- Set `runtime: image` and `image.url` to full reference (tag or digest).
- Add `registryCredential` when registry is private.

Immutable deploys:

```yaml
image:
  url: ghcr.io/myorg/api@sha256:abc123...
```

---

## Auto-deploy and prebuilt images

Services that **only pull** prebuilt image (`runtime: image`) **do not** auto-deploy when mutable tag like `latest` updates upstream. After publishing new image, you must:

- Trigger manual redeploy in Dashboard, or
- Call deploy hook / API flow your team uses for CD.

Pair immutable tags or digests with release pipeline so each deploy points at explicit artifact.
