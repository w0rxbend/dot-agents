# Secret Management Integration

## Table of Contents

- [Sealed Secrets](#sealed-secrets)
  - [Installation](#installation)
  - [Create Sealed Secret](#create-sealed-secret)
  - [Sealed Secret Manifest](#sealed-secret-manifest)
- [External Secrets Operator](#external-secrets-operator)
  - [Installation](#installation)
  - [Vault SecretStore](#vault-secretstore)
  - [ExternalSecret](#externalsecret)
- [SOPS Encryption](#sops-encryption)
  - [Installation](#installation)
  - [Encrypt File with SOPS](#encrypt-file-with-sops)
  - [Flux SOPS Integration](#flux-sops-integration)

## Sealed Secrets

### Installation

```bash
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Install kubeseal CLI
brew install kubeseal
```

### Create Sealed Secret

```bash
# Create and seal in one pipe: value read from stdin (not shell history or
# process args), no plaintext secret.yaml left in the working tree
read -rs PASSWORD
printf '%s' "$PASSWORD" | kubectl create secret generic mysecret -n myapp \
  --from-file=password=/dev/stdin \
  --dry-run=client -o yaml | kubeseal -o yaml > sealedsecret.yaml
unset PASSWORD

# Commit sealed secret to Git
git add sealedsecret.yaml
git commit -m "Add sealed secret"
```

### Sealed Secret Manifest

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: mysecret
  namespace: myapp
spec:
  encryptedData:
    password: AgBy3i4OJSWK+PiTySY...
```

## External Secrets Operator

### Installation

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --version 2.14.0 -n external-secrets-system --create-namespace
```

### Vault SecretStore

```yaml
apiVersion: external-secrets.io/v1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: myapp
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "myapp"
```

### ExternalSecret

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: myapp-secrets
  namespace: myapp
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: myapp-secrets
    creationPolicy: Owner
  data:
  - secretKey: database-password
    remoteRef:
      key: secret/myapp/database
      property: password
  - secretKey: api-key
    remoteRef:
      key: secret/myapp/api
      property: key
```

## SOPS Encryption

### Installation

```bash
# Install SOPS
brew install sops

# Install age for encryption
brew install age

# Generate age key outside the repo; never commit it
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/keys.txt
```

### Encrypt File with SOPS

```yaml
# secrets/prod-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secrets
stringData:
  database-url: postgresql://prod-db:5432/myapp
  api-key: sk_prod_abc123xyz
```

```bash
# Encrypt in place with the age public key, so no plaintext copy remains;
# never commit the file before it is encrypted
sops --encrypt --in-place --age "$(age-keygen -y ~/.config/sops/age/keys.txt)" secrets/prod-secrets.yaml

# Commit encrypted file
git add secrets/prod-secrets.yaml
```

### Flux SOPS Integration

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: myapp-secrets
  namespace: flux-system
spec:
  interval: 10m
  path: ./secrets
  prune: true
  sourceRef:
    kind: GitRepository
    name: myapp
  decryption:
    provider: sops
    secretRef:
      name: sops-age
```

The decryption key must never live in Git. Create the `sops-age` secret out of band:

```bash
kubectl create secret generic sops-age -n flux-system \
  --from-file=age.agekey=$HOME/.config/sops/age/keys.txt
```
