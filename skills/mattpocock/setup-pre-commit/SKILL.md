---
name: setup-pre-commit
description: Set up Husky pre-commit hooks with lint-staged (Prettier), type checking, and tests in the current repo. Use when user wants to add pre-commit hooks, set up Husky, configure lint-staged, or add commit-time formatting/typechecking/testing.
disable-model-invocation: true
---

# Setup Pre-Commit Hooks

## Steps

### 1. Detect package manager

Check for `package-lock.json` (npm), `pnpm-lock.yaml` (pnpm), `yarn.lock` (yarn), `bun.lock` or `bun.lockb` (bun; Bun 1.2+ writes text lockfile `bun.lock`). Use whichever exists. Default to npm if unclear.

### 2. Install dependencies

Install as devDependencies:

```
husky lint-staged prettier
```

### 3. Initialize Husky

```bash
npx husky init
```

Creates `.husky/` dir and adds `prepare: "husky"` to package.json.

### 4. Create `.husky/pre-commit`

Write this file (Husky v9+ needs no shebang):

```
npx lint-staged
npm run typecheck
npm run test
```

Hook runs lint-staged first (fast, staged-only), then full typecheck and tests.

**Adapt**: Replace `npm` with detected package manager. If package.json has no `typecheck` or `test` script, omit those lines and tell user.

### 5. Create `.lintstagedrc`

```json
{
  "*": "prettier --ignore-unknown --write"
}
```

`prettier --ignore-unknown` skips files Prettier can't parse (images, etc.).

### 6. Create `.prettierrc` (if missing)

Create only if no Prettier config exists. Defaults:

```json
{
  "useTabs": false,
  "tabWidth": 2,
  "printWidth": 80,
  "singleQuote": false,
  "trailingComma": "es5",
  "semi": true,
  "arrowParens": "always"
}
```

### 7. Verify

- [ ] `.husky/pre-commit` exists and is executable
- [ ] `.lintstagedrc` exists
- [ ] `prepare` script in package.json is `"husky"`
- [ ] `prettier` config exists
- [ ] Run `npx lint-staged` to confirm it works

### 8. Commit

Ask user before committing. If user agrees, stage only files this skill created or changed (`.husky/pre-commit`, `.lintstagedrc`, `.prettierrc` if created, `package.json`, lockfile). Do not stage unrelated work in tree. Commit with message: `Add pre-commit hooks (husky + lint-staged + prettier)`

Commit runs new pre-commit hooks: good smoke test. Do not push.
