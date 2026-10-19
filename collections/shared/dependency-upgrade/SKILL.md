---
name: dependency-upgrade
description: "Plan and execute a major JavaScript/npm dependency version upgrade (examples use npm, React and TypeScript) - semver and breaking-change review, compatibility matrix, one-major-at-a-time staged rollout, and test/verification strategy. Use when bumping an npm dependency across a major version or a JS framework migration; for Go modules use golang-dependency-management; use dependency-scanning to find which dependencies are vulnerable."
risk: critical
source: community
date_added: "2026-02-27"
---

# Dependency Upgrade

Major dependency version upgrades for JavaScript/npm projects: compatibility analysis, staged upgrade strategies, and testing approaches. The method (one major at a time, read the changelog, baseline tests first) carries over to other ecosystems; the commands do not.

## Use this skill when

- Upgrading major framework versions
- Updating security-vulnerable dependencies
- Modernizing legacy dependencies
- Resolving dependency conflicts
- Planning incremental upgrade paths
- Testing compatibility matrices
- Automating dependency updates

## Semantic Versioning Review

```
MAJOR.MINOR.PATCH (e.g., 2.3.1)

MAJOR: Breaking changes
MINOR: New features, backward compatible
PATCH: Bug fixes, backward compatible

^2.3.1 = >=2.3.1 <3.0.0 (minor updates)
~2.3.1 = >=2.3.1 <2.4.0 (patch updates)
2.3.1 = exact version
```

## Dependency Analysis

### Audit Dependencies
```bash
# npm
npm outdated
npm audit
npm audit fix

# yarn
yarn outdated
yarn audit

# Check for major updates
npx npm-check-updates
npx npm-check-updates -u  # Update package.json
```

### Analyze Dependency Tree
```bash
# See why a package is installed
npm ls package-name
yarn why package-name

# Find duplicate packages
npm dedupe
yarn dedupe

# Visualize dependencies
npx madge --image graph.png src/
```

## Compatibility Matrix

```javascript
// compatibility-matrix.js
const compatibilityMatrix = {
  'react': {
    '16.x': {
      'react-dom': '^16.0.0',
      'react-router-dom': '^5.0.0',
      '@testing-library/react': '^11.0.0'
    },
    '17.x': {
      'react-dom': '^17.0.0',
      'react-router-dom': '^5.0.0 || ^6.0.0',
      '@testing-library/react': '^12.0.0'
    },
    '18.x': {
      'react-dom': '^18.0.0',
      'react-router-dom': '^6.0.0',
      '@testing-library/react': '^13.0.0'
    }
  }
};

function checkCompatibility(packages) {
  // Validate package versions against matrix
}
```

## Staged Upgrade Strategy

### Phase 1: Planning
```bash
# 1. Identify current versions
npm list --depth=0

# 2. Check for breaking changes
# Read CHANGELOG.md and MIGRATION.md

# 3. Create upgrade plan
echo "Upgrade order:
1. TypeScript
2. React
3. React Router
4. Testing libraries
5. Build tools" > UPGRADE_PLAN.md
```

### Phase 2: Incremental Updates
```bash
# Don't upgrade everything at once!

# Step 1: Update TypeScript
npm install typescript@latest

# Test
npm run test
npm run build

# Step 2: Update React (one major version at a time)
npm install react@17 react-dom@17

# Test again
npm run test

# Step 3: Continue with other packages
npm install react-router-dom@6

# And so on...
```

### Phase 3: Validation
```javascript
// tests/compatibility.test.js
describe('Dependency Compatibility', () => {
  it('should have compatible React versions', () => {
    const reactVersion = require('react/package.json').version;
    const reactDomVersion = require('react-dom/package.json').version;

    expect(reactVersion).toBe(reactDomVersion);
  });

  it('should not have peer dependency warnings', () => {
    // Run npm ls and check for warnings
  });
});
```

## Breaking Change Handling

### Identifying Breaking Changes
```bash
# Read the changelog / release notes between your current and target versions
curl -fsSL https://raw.githubusercontent.com/facebook/react/main/CHANGELOG.md | less
gh release list --repo facebook/react

# Upstream migration guides (e.g. react.dev/blog "React 19 Upgrade Guide") list the breaking changes
```

### Codemod for Automated Fixes
```bash
# React upgrade codemods (react-codemod, runs jscodeshift)
npx react-codemod <transform> <path>

# Example: rename deprecated lifecycle methods
npx react-codemod rename-unsafe-lifecycles src/
```

### Custom Migration Script
```javascript
// migration-script.js
const fs = require('fs');
const { globSync } = require('glob'); // glob >= 9 has no callback API

globSync('src/**/*.tsx').forEach(file => {
    let content = fs.readFileSync(file, 'utf8');

    // Replace old API with new API
    content = content.replace(
      /componentWillMount/g,
      'UNSAFE_componentWillMount'
    );

    // Update imports
    content = content.replace(
      /import { Component } from 'react'/g,
      "import React, { Component } from 'react'"
    );

    fs.writeFileSync(file, content);
});
```

## Testing Strategy

### Unit Tests
```javascript
// Ensure tests pass before and after upgrade
npm run test

// Update test utilities if needed
npm install @testing-library/react@latest
```

### Integration Tests
```javascript
// tests/integration/app.test.js
describe('App Integration', () => {
  it('should render without crashing', () => {
    render(<App />);
  });

  it('should handle navigation', () => {
    const { getByText } = render(<App />);
    fireEvent.click(getByText('Navigate'));
    expect(screen.getByText('New Page')).toBeInTheDocument();
  });
});
```

### Visual Regression Tests
```javascript
// visual-regression.test.js
describe('Visual Regression', () => {
  it('should match snapshot', () => {
    const { container } = render(<App />);
    expect(container.firstChild).toMatchSnapshot();
  });
});
```

### E2E Tests
```javascript
// cypress/e2e/app.cy.js
describe('E2E Tests', () => {
  it('should complete user flow', () => {
    cy.visit('/');
    cy.get('[data-testid="login"]').click();
    cy.get('input[name="email"]').type('user@example.com');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');
  });
});
```

## Automated Dependency Updates

### Renovate Configuration
```json
// renovate.json
{
  "extends": ["config:recommended"],
  "packageRules": [
    {
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": true
    },
    {
      "matchUpdateTypes": ["major"],
      "automerge": false,
      "labels": ["major-update"]
    }
  ],
  "schedule": ["before 3am on Monday"],
  "timezone": "America/New_York"
}
```

### Dependabot Configuration
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    # assign reviewers via CODEOWNERS (the `reviewers:` key is deprecated)
    commit-message:
      prefix: "chore"
      include: "scope"
```

## Rollback Plan

Do the upgrade in a separate worktree so uncommitted work in the main checkout is never touched, and leave cleanup to an explicit, confirmed step.

```bash
#!/usr/bin/env bash
# upgrade-in-worktree.sh <package> [version]
set -euo pipefail
pkg="$1"; ver="${2:-latest}"
base="$(git rev-parse --abbrev-ref HEAD)"
branch="upgrade/${pkg//\//-}-${ver}"
dir="../upgrade-${pkg//\//-}"

git worktree add -b "$branch" "$dir" "$base"
cd "$dir"
npm ci
npm install "${pkg}@${ver}"

if npm test; then
  echo "Upgrade passed tests on branch $branch in $dir - review the diff, then commit when ready."
else
  echo "Upgrade failed. Nothing in your main checkout changed."
  echo "To discard it (after confirming you no longer need it):"
  echo "  git worktree remove $dir && git branch -D $branch"
fi
```

## Common Upgrade Patterns

### Lock File Management
```bash
# npm
npm install --package-lock-only  # Update lock file only
npm ci  # Clean install from lock file

# yarn
yarn install --frozen-lockfile  # CI mode
yarn upgrade-interactive  # Interactive upgrades
```

### Peer Dependency Resolution
```bash
# npm 7+: strict peer dependencies
npm install --legacy-peer-deps  # Ignore peer deps

# npm 8+: override peer dependencies
npm install --force
```

### Workspace Upgrades
```bash
# Update all workspace packages
npm install --workspaces

# Update specific workspace
npm install package@latest --workspace=packages/app
```

## Resources

Use the dependency manifests, lockfiles, upstream migration guides, and the staged procedure above. This installation does not ship separate compatibility matrices or an audit-dependencies.sh helper.

## Best Practices

1. **Read Changelogs**: Understand what changed
2. **Upgrade Incrementally**: One major version at a time
3. **Test Thoroughly**: Unit, integration, E2E tests
4. **Check Peer Dependencies**: Resolve conflicts early
5. **Use Lock Files**: Ensure reproducible installs
6. **Automate Updates**: Use Renovate or Dependabot
7. **Monitor**: Watch for runtime errors post-upgrade
8. **Document**: Keep upgrade notes

## Upgrade Checklist

```markdown
Pre-Upgrade:
- [ ] Review current dependency versions
- [ ] Read changelogs for breaking changes
- [ ] Create feature branch
- [ ] Backup current state (git tag)
- [ ] Run full test suite (baseline)

During Upgrade:
- [ ] Upgrade one dependency at a time
- [ ] Update peer dependencies
- [ ] Fix TypeScript errors
- [ ] Update tests if needed
- [ ] Run test suite after each upgrade
- [ ] Check bundle size impact

Post-Upgrade:
- [ ] Full regression testing
- [ ] Performance testing
- [ ] Update documentation
- [ ] Deploy to staging
- [ ] Monitor for errors
- [ ] Deploy to production
```

## Common Pitfalls

- Upgrading all dependencies at once
- Not testing after each upgrade
- Ignoring peer dependency warnings
- Forgetting to update lock file
- Not reading breaking change notes
- Skipping major versions
- Not having rollback plan

